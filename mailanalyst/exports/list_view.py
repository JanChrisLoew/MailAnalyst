"""A streaming projection using the shared review column mapping."""

import pandas as pd

from mailanalyst.record_store import RecordStore
from mailanalyst.exports.tabular import list_export_dataframe


class ListView(RecordStore):
    def __init__(self, store):
        self.store = store
        probe = list_export_dataframe(pd.DataFrame([{key: key for key in store.columns}]))
        self.mapping = {name: probe.iloc[0][name] for name in probe.columns}
        self.columns = {name: store.columns[key] for name, key in self.mapping.items()}
        self.count, self.batch_size, self.cancel = len(store), store.batch_size, store.cancel

    def records(self, chunk=None):
        for row in self.store.records(chunk):
            yield {name: row[key] for name, key in self.mapping.items()}
