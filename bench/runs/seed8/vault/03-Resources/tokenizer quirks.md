# tokenizer quirks

## whitespace and leading spaces
- " hello" and "hello" are different tokens. Always check whether a prompt template ends with a trailing space, it shifts the next-token distribution noticeably.
- Newlines are often their own tokens, and runs of them can merge into one. "\n\n" is usually not two "\n".
- Tabs vs 4 spaces: tabs are cheaper in most vocabularies. Matters for code-heavy prompts when I'm counting budget.
- Stripping input before tokenizing fixes ~half of the "why does this give different output" bugs.

## counting and budgeting
- Rough rule: ~4 chars per token for English, ~3 for code, worse for anything non-Latin. Don't trust it for limits, use the real tokenizer.
- Always count tokens on the final rendered string, after the chat template is applied. Special tokens add up.
- JSON is expensive. Quotes, braces and repeated keys all burn tokens. Compact separators (no spaces after `:` and `,`) saved me about 10-15% on one payload.
- Numbers split unpredictably. "1234567" might be 2-4 tokens depending on the vocab. Don't assume digit-level splitting.
- UUIDs and hashes are token-hungry, nearly one token per 2 chars. Truncate them in logs and prompts when possible.

## special tokens
- User text containing something like `<|endoftext|>` may get parsed as a real special token unless I disable that. Check the `allowed_special` / `disallowed_special` style flags.
- BOS/EOS handling differs by library. Double encoding BOS (template adds one, tokenizer adds another) is a classic silent bug.
- Padding side matters: left pad for generation, right pad for training. Forgot this once and spent an hour on garbage outputs.
- Pad token is often unset by default, so set it explicitly (usually to EOS) before batching.

## roundtrip gotchas
- decode(encode(x)) != x in some cases: unicode normalization, byte fallback, and stripped spaces in "clean up tokenization" options.
- Partial decoding of streamed tokens can produce broken characters (�) when a multibyte char is split across tokens. Buffer until the string decodes cleanly.
- Emoji and some CJK chars are multiple byte-level tokens, so truncating by token count can cut mid-character.
- Case matters: "The" vs "the" vs "THE" all tokenize differently, and all caps is usually more tokens.

## debugging checklist
1. Print the token ids AND the decoded pieces side by side.
2. Check for a trailing space or newline.
3. Confirm the tokenizer version matches the model checkpoint.
4. Compare against the reference tokenizer on 5 weird strings (emoji, tabs, long digits, mixed script, empty string).
5. Check the special token flags.
