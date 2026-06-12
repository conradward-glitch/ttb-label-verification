# Hermes Troubleshooting Notes

## 2026-06-11 — Startup/API failure after unsupported Codex model selection

### Summary

Hermes started, but conversation turns failed immediately when using the `openai-codex` provider with the model set to `gpt-5.3-codex`.

The failure was not caused by WSL, the terminal, missing files, or a broken Hermes install. The configured model was not supported for the current ChatGPT-backed Codex account.

### Symptoms

Observed in `~/.hermes/logs/errors.log`:

```text
2026-06-11 21:43:37,235 WARNING ... provider=openai-codex base_url=https://chatgpt.com/backend-api/codex model=gpt-5.3-codex summary=HTTP 400: Error code: 400 - {'detail': "The 'gpt-5.3-codex' model is not supported when using Codex with a ChatGPT account."}
2026-06-11 21:43:37,246 ERROR ... Non-retryable client error: Error code: 400 - {'detail': "The 'gpt-5.3-codex' model is not supported when using Codex with a ChatGPT account."}
```

The same unsupported-model error repeated during later attempts at approximately:

- `2026-06-11 21:29:05 EDT`
- `2026-06-11 21:43:37 EDT`
- `2026-06-11 21:54:41 EDT`

### Root cause

`~/.hermes/config.yaml` was configured to use:

```yaml
model:
  provider: openai-codex
  default: gpt-5.3-codex
```

That model is not available through the ChatGPT-account Codex backend. The provider returned HTTP 400, and Hermes correctly treated it as a non-retryable client/configuration error.

### Fix applied

Change the active Hermes model to a supported Codex model.

Current verified working configuration:

```yaml
model:
  provider: openai-codex
  default: gpt-5.5
```

Recommended command if this happens again:

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5
```

Then restart Hermes:

```bash
exit
hermes
```

Or use the interactive picker:

```bash
hermes model
```

### Verification

After the fix, check the active config:

```bash
hermes config path
python3 - <<'PY'
import os, yaml
p = os.path.expanduser('~/.hermes/config.yaml')
d = yaml.safe_load(open(p, encoding='utf-8-sig')) or {}
print('provider:', (d.get('model') or {}).get('provider'))
print('model:', (d.get('model') or {}).get('default'))
PY
```

Expected output:

```text
provider: openai-codex
model: gpt-5.5
```

Also check logs for repeated startup/API failures:

```bash
grep -i "not supported\|non-retryable\|badrequest\|HTTP 400" ~/.hermes/logs/errors.log | tail -20
```

### Prevention steps

1. Use `hermes model` when changing providers/models instead of hand-editing `config.yaml`.
2. After selecting a new model, run a quick smoke test:

   ```bash
   hermes chat -q "reply with ok"
   ```

3. If Hermes fails immediately after a model change, inspect:

   ```bash
   tail -50 ~/.hermes/logs/errors.log
   ```

4. Treat HTTP 400 errors from the model provider as configuration problems first, not network or install problems.
5. Keep a known-good fallback model documented. For this machine, the current fallback is:

   ```text
   provider: openai-codex
   model: gpt-5.5
   ```

### Quick recovery checklist

```bash
# 1. Confirm the failure
tail -50 ~/.hermes/logs/errors.log

# 2. Reset to known-good Codex model
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5

# 3. Restart Hermes
exit
hermes

# 4. Smoke test if using one-shot mode
hermes chat -q "reply with ok"
```

### Notes

- This was a model/provider compatibility issue.
- No evidence pointed to a broken Hermes install.
- No evidence pointed to WSL or Windows filesystem problems.
- The important diagnostic string is:

```text
The 'gpt-5.3-codex' model is not supported when using Codex with a ChatGPT account.
```
