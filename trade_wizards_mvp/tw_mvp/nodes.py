from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class GraphResult:
    node_outputs: dict[str, pd.Series]
    entry_signal: pd.Series
    exit_signal: pd.Series


def _as_series(value: Any, index: pd.Index) -> pd.Series:
    if isinstance(value, pd.Series):
        return value.reindex(index)
    return pd.Series([value] * len(index), index=index)


def _parse_target_lag_days(target_name: str) -> int:
    match = re.search(r"(\d+)d$", target_name)
    if match:
        return int(match.group(1))
    return 1


def _rsi_per_ticker(series: pd.Series, ticker: pd.Series, window: int) -> pd.Series:
    tmp = pd.DataFrame({"ticker": ticker.to_numpy(), "v": series.to_numpy()}, index=series.index)

    def _calc(g: pd.Series) -> pd.Series:
        diff = g.diff()
        gain = diff.clip(lower=0.0)
        loss = -diff.clip(upper=0.0)
        avg_gain = gain.ewm(alpha=1.0 / window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / window, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    return tmp.groupby("ticker", sort=False)["v"].transform(_calc)


def _rolling_group_transform(
    values: pd.Series,
    ticker: pd.Series,
    window: int,
    mode: str,
) -> pd.Series:
    tmp = pd.DataFrame({"ticker": ticker.to_numpy(), "v": values.to_numpy()}, index=values.index)

    if mode == "sma":
        return tmp.groupby("ticker", sort=False)["v"].transform(
            lambda s: s.rolling(window=window, min_periods=window).mean()
        )
    if mode == "ema":
        return tmp.groupby("ticker", sort=False)["v"].transform(lambda s: s.ewm(span=window, adjust=False).mean())
    if mode == "zscore":
        mean = tmp.groupby("ticker", sort=False)["v"].transform(
            lambda s: s.rolling(window=window, min_periods=window).mean()
        )
        std = tmp.groupby("ticker", sort=False)["v"].transform(
            lambda s: s.rolling(window=window, min_periods=window).std(ddof=0)
        )
        out = (values - mean) / std.replace(0.0, np.nan)
        return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if mode == "return":
        return tmp.groupby("ticker", sort=False)["v"].transform(lambda s: s.pct_change(window))

    raise ValueError(f"Unsupported rolling mode: {mode}")


def _fit_predict_mlp_probability(
    frame: pd.DataFrame,
    date_col: str,
    feature_cols: list[str],
    target_col: str,
    train_window_days: int,
    retrain_every_days: int,
    label_lag_days: int,
    min_train_rows: int,
    hidden_layer_sizes: tuple[int, ...],
    max_iter: int,
    random_state: int,
) -> pd.Series:
    dates = np.array(sorted(pd.to_datetime(frame[date_col]).dropna().unique()))
    out = pd.Series(np.nan, index=frame.index, dtype="float64")
    if len(dates) < train_window_days + label_lag_days + 10:
        return out

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=hidden_layer_sizes,
                    activation="relu",
                    solver="adam",
                    alpha=1e-4,
                    learning_rate_init=1e-3,
                    max_iter=max_iter,
                    random_state=random_state,
                ),
            ),
        ]
    )

    start_idx = train_window_days + label_lag_days
    while start_idx < len(dates):
        train_end_idx = start_idx - label_lag_days
        train_start_idx = max(0, train_end_idx - train_window_days)
        train_dates = dates[train_start_idx:train_end_idx]
        pred_end_idx = min(start_idx + retrain_every_days, len(dates))
        pred_dates = dates[start_idx:pred_end_idx]

        train_mask = frame[date_col].isin(train_dates) & frame[target_col].notna()
        pred_mask = frame[date_col].isin(pred_dates)

        if train_mask.sum() < min_train_rows or pred_mask.sum() == 0:
            start_idx += retrain_every_days
            continue

        x_train = frame.loc[train_mask, feature_cols]
        y_train = frame.loc[train_mask, target_col].astype(int)
        if y_train.nunique() < 2:
            start_idx += retrain_every_days
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(x_train, y_train)

        x_pred = frame.loc[pred_mask, feature_cols]
        proba = model.predict_proba(x_pred)[:, 1]
        out.loc[pred_mask] = proba

        start_idx += retrain_every_days

    return out


class NodeGraphEngine:
    def __init__(self, graph_cfg: dict[str, Any]) -> None:
        nodes = graph_cfg.get("nodes", [])
        signals = graph_cfg.get("signals", {})
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("graph.nodes must be a non-empty list.")
        if not isinstance(signals, dict):
            raise ValueError("graph.signals must be a dict.")

        self.nodes: list[dict[str, Any]] = nodes
        self.entry_ref = signals.get("entry")
        self.exit_ref = signals.get("exit")
        if not self.entry_ref or not self.exit_ref:
            raise ValueError("graph.signals must define both 'entry' and 'exit'.")

    def _resolve_ref(self, ref: Any, frame: pd.DataFrame, ctx: dict[str, pd.Series]) -> pd.Series:
        if isinstance(ref, str):
            if ref in ctx:
                return ctx[ref]
            if ref in frame.columns:
                return frame[ref]
            raise ValueError(f"Unknown reference: '{ref}'")
        return _as_series(ref, index=frame.index)

    def _eval_indicator(self, node: dict[str, Any], frame: pd.DataFrame, ctx: dict[str, pd.Series]) -> pd.Series:
        indicator = str(node.get("indicator", "")).strip().lower()
        if indicator == "column":
            column = str(node.get("column", "")).strip()
            if not column:
                raise ValueError(f"Node '{node['id']}' indicator=column requires 'column'.")
            return self._resolve_ref(column, frame, ctx)

        source_ref = node.get("source", "close")
        source = pd.to_numeric(self._resolve_ref(source_ref, frame, ctx), errors="coerce")
        window = int(node.get("window", 20))
        if window <= 0:
            raise ValueError(f"Node '{node['id']}' has invalid window={window}")

        if indicator in {"sma", "ema", "zscore", "return"}:
            return _rolling_group_transform(values=source, ticker=frame["ticker"], window=window, mode=indicator)
        if indicator == "rsi":
            return _rsi_per_ticker(series=source, ticker=frame["ticker"], window=window)

        raise ValueError(f"Node '{node['id']}' has unsupported indicator='{indicator}'.")

    def _eval_compare(self, node: dict[str, Any], frame: pd.DataFrame, ctx: dict[str, pd.Series]) -> pd.Series:
        op = str(node.get("op", "==")).strip()
        left = self._resolve_ref(node.get("left"), frame, ctx)
        right = self._resolve_ref(node.get("right"), frame, ctx)
        left_num = pd.to_numeric(left, errors="coerce")
        right_num = pd.to_numeric(right, errors="coerce")

        if op == ">":
            out = left_num > right_num
        elif op == ">=":
            out = left_num >= right_num
        elif op == "<":
            out = left_num < right_num
        elif op == "<=":
            out = left_num <= right_num
        elif op == "==":
            out = left_num == right_num
        elif op == "!=":
            out = left_num != right_num
        else:
            raise ValueError(f"Node '{node['id']}' has unsupported compare op='{op}'.")
        return out.fillna(False).astype(bool)

    def _eval_logic(self, node: dict[str, Any], frame: pd.DataFrame, ctx: dict[str, pd.Series]) -> pd.Series:
        op = str(node.get("op", "and")).strip().lower()
        inputs = node.get("inputs", [])
        if not isinstance(inputs, list) or not inputs:
            raise ValueError(f"Node '{node['id']}' logic requires non-empty 'inputs'.")
        resolved = [self._resolve_ref(ref, frame, ctx).fillna(False).astype(bool) for ref in inputs]

        if op == "and":
            out = resolved[0].copy()
            for cur in resolved[1:]:
                out = out & cur
            return out
        if op == "or":
            out = resolved[0].copy()
            for cur in resolved[1:]:
                out = out | cur
            return out
        if op == "xor":
            out = resolved[0].copy()
            for cur in resolved[1:]:
                out = out ^ cur
            return out
        if op == "not":
            if len(resolved) != 1:
                raise ValueError(f"Node '{node['id']}' logic op='not' expects exactly 1 input.")
            return ~resolved[0]

        raise ValueError(f"Node '{node['id']}' has unsupported logic op='{op}'.")

    def _eval_math(self, node: dict[str, Any], frame: pd.DataFrame, ctx: dict[str, pd.Series]) -> pd.Series:
        op = str(node.get("op", "add")).strip().lower()
        left = pd.to_numeric(self._resolve_ref(node.get("left"), frame, ctx), errors="coerce")
        right = pd.to_numeric(self._resolve_ref(node.get("right"), frame, ctx), errors="coerce")

        if op == "add":
            return left + right
        if op == "sub":
            return left - right
        if op == "mul":
            return left * right
        if op == "div":
            return left / right.replace(0.0, np.nan)
        if op == "max":
            return pd.concat([left, right], axis=1).max(axis=1)
        if op == "min":
            return pd.concat([left, right], axis=1).min(axis=1)
        raise ValueError(f"Node '{node['id']}' has unsupported math op='{op}'.")

    def _eval_neural_net(self, node: dict[str, Any], frame: pd.DataFrame, ctx: dict[str, pd.Series]) -> pd.Series:
        feature_refs = node.get("features", [])
        if not isinstance(feature_refs, list) or not feature_refs:
            raise ValueError(f"Node '{node['id']}' neural_net requires a non-empty features list.")

        target_ref = str(node.get("target", "target_up_5d"))
        train_window_days = int(node.get("train_window_days", 252))
        retrain_every_days = int(node.get("retrain_every_days", 21))
        min_train_rows = int(node.get("min_train_rows", 1_500))
        hidden_layer_sizes = tuple(int(x) for x in node.get("hidden_layer_sizes", [16, 8]))
        max_iter = int(node.get("max_iter", 180))
        random_state = int(node.get("random_state", 42))
        label_lag_days = int(node.get("label_lag_days", _parse_target_lag_days(target_ref)))

        if train_window_days <= 0 or retrain_every_days <= 0:
            raise ValueError(f"Node '{node['id']}' has invalid train/retrain window params.")

        feature_frame = pd.DataFrame(index=frame.index)
        feature_cols: list[str] = []
        for idx, ref in enumerate(feature_refs):
            col_name = f"f_{idx}"
            feature_frame[col_name] = pd.to_numeric(self._resolve_ref(ref, frame, ctx), errors="coerce")
            feature_cols.append(col_name)

        target_series = pd.to_numeric(self._resolve_ref(target_ref, frame, ctx), errors="coerce")
        train_df = feature_frame.copy()
        train_df["date"] = pd.to_datetime(frame["date"], errors="coerce")
        train_df[target_ref] = target_series

        out = _fit_predict_mlp_probability(
            frame=train_df,
            date_col="date",
            feature_cols=feature_cols,
            target_col=target_ref,
            train_window_days=train_window_days,
            retrain_every_days=retrain_every_days,
            label_lag_days=label_lag_days,
            min_train_rows=min_train_rows,
            hidden_layer_sizes=hidden_layer_sizes,
            max_iter=max_iter,
            random_state=random_state,
        )
        return out

    def evaluate(self, frame: pd.DataFrame) -> GraphResult:
        required = {"date", "ticker"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"Input frame missing required columns: {missing}")

        frame = frame.sort_values(["date", "ticker"]).reset_index(drop=True)
        ctx: dict[str, pd.Series] = {}

        for node in self.nodes:
            node_id = str(node.get("id", "")).strip()
            node_type = str(node.get("type", "")).strip().lower()
            if not node_id or not node_type:
                raise ValueError(f"Each node requires non-empty 'id' and 'type'. Got: {node}")
            if node_id in ctx:
                raise ValueError(f"Duplicate node id detected: {node_id}")

            if node_type == "indicator":
                out = self._eval_indicator(node, frame, ctx)
            elif node_type == "compare":
                out = self._eval_compare(node, frame, ctx)
            elif node_type == "logic":
                out = self._eval_logic(node, frame, ctx)
            elif node_type == "math":
                out = self._eval_math(node, frame, ctx)
            elif node_type == "neural_net":
                out = self._eval_neural_net(node, frame, ctx)
            else:
                raise ValueError(f"Node '{node_id}' has unsupported type='{node_type}'.")

            ctx[node_id] = _as_series(out, index=frame.index)

        entry = self._resolve_ref(self.entry_ref, frame, ctx).fillna(False).astype(bool)
        exit_ = self._resolve_ref(self.exit_ref, frame, ctx).fillna(False).astype(bool)
        return GraphResult(node_outputs=ctx, entry_signal=entry, exit_signal=exit_)

