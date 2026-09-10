"""Bind selected source content to its preflight fingerprint."""


def require_preflight(signature, expected):
    if expected is None:
        return
    actual = (signature.file_size, signature.modified_at_ns, signature.file_sha256)
    if not expected[2] or actual != expected:
        raise RuntimeError(f"Quelle seit der Vorpruefung geaendert oder ungeprueft; erneut pruefen: {signature.key}")
