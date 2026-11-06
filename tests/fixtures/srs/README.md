# SRS fixtures

These files were generated with `sing-box 1.14.4`:

```sh
sing-box rule-set compile <case>.json
```

Tests compare the decompressed payload, not the compressed bytes, because Go
and Python zlib implementations may produce different valid streams for the
same payload.

Do not regenerate these files unless the SRS format or the sing-box rule-set
serializer changes.
