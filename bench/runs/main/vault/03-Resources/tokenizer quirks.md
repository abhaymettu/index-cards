# tokenizer quirks

## whitespace and leading spaces
- " hello" and "hello" are different tokens. Most BPE vocabs bake the leading space into the token. Easy to get off-by-one when slicing prompts by token count.
- Trailing whitespace in a prompt can push the model into weird continuations. Always strip before sending unless I really want the space.
- Multiple spaces / tabs often collapse into special run-length tokens. Indented code tokenizes cheaper than I expected, but mixed tabs and spaces tokenize badly.
- Newline handling: "\n\n" is often a single token, "\n\n\n" may not be. Don't assume concatenation of tokens = tokens of concatenation.

## encode/decode roundtrip
- decode(encode(x)) == x is NOT guaranteed with some tokenizers (normalization, unicode NFC/NFKC, stripped control chars). Test with emoji, combining accents, zero-width joiner.
- Decoding a partial token sequence (streaming) can yield broken UTF-8 and show replacement chars. Buffer bytes until valid, don't decode per token.
- Byte-level fallback means any string encodes, but weird input can blow up token count 3-4x.

## counting and budgets
- Chars/4 heuristic is fine for English prose, bad for code, JSON, non-Latin scripts, and long numbers.
- Numbers split unpredictably: "12345" might be 2 tokens, "12346" might be 3. Don't build logic around digit boundaries.
- JSON with lots of quotes, braces, and short keys is token-heavy. Minified isn't always cheaper than pretty-printed since whitespace runs merge.
- Always count with the exact tokenizer for the target model. Different versions of the "same" family can differ.
- Leave headroom: count prompt + max output + a margin for special/chat-template tokens (role markers, end tokens add up).

## special tokens
- User text containing something like "<|endoftext|>" may get parsed as a real special token depending on flags. Check the allowed_special / disallowed_special setting and sanitize untrusted input.
- Chat templates add BOS/EOS differently per model. Double BOS silently hurts quality. Check whether the tokenizer call already adds it before adding manually.
- Padding side matters: left-pad for generation, right-pad for training batches.

## debugging checklist
1. Print the token ids AND the decoded pieces side by side.
2. Check for a leading-space mismatch.
3. Check special-token parsing flags.
4. Confirm tokenizer version matches the model checkpoint.
5. Compare with a known-good string to rule out my own preprocessing.
