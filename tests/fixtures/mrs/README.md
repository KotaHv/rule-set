# MRS fixtures

These files were generated with `mihomo 1.19.33`:

```sh
mihomo convert-ruleset domain yaml domain.yaml domain.mrs
mihomo convert-ruleset domain yaml domain_unicode.yaml domain_unicode.mrs
mihomo convert-ruleset ipcidr yaml ipcidr.yaml ipcidr.mrs
```

Tests compare the decompressed payload, not the compressed bytes, because Go
and Python zstd implementations may produce different valid streams for the
same payload.

`domain_unicode.yaml` also covers Python's context-sensitive lowercasing:
`İ` expands to two code points under `str.lower()`, and a domain ending in `Σ`
would become final sigma. The encoder must match Go's per-rune mapping instead.

Do not regenerate these files unless the MRS format or the mihomo rule-set
serializer changes.
