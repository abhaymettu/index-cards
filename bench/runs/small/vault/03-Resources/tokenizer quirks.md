# tokenizer quirks

## whitespace and leading spaces
- most BPE vocabs treat " hello" and "hello" as different tokens. leading space is baked into the token. so prompt that ends with a trailing space = bad, model has to predict a token that normally *includes* the space
- strip trailing whitespace on prompts before sending. learned this the annoying way, outputs got weirdly terse
- multiple spaces / tabs often collapse into their own tokens. indented code costs more than you'd think
- newline runs ("\n\n\n") sometimes one token, sometimes several. depends on vocab, check don't assume

## counting tokens
- never estimate with len(text)/4 for anything that matters. fine for napkin math only
- non-English text, emoji, and rare unicode blow up the count. a single emoji can be 2–4 tokens
- numbers split in odd ways. "1234567" might be "123" "456" "7". explains why arithmetic and digit-level tasks are flaky
- JSON is expensive: quotes, braces, and repeated keys all add up. compact keys or send CSV-ish if budget is tight
- always count with the actual tokenizer for the target model. different families = different counts, even on same text

## special tokens
- user text containing something like `<|endoftext|>` may get parsed as a real special token depending on the encode flag. check `allowed_special` / `disallowed_special` behavior in the lib
- sanitize user input before encoding if the template uses special markers. otherwise injection through the chat template is possible
- BOS/EOS get added automatically by some tokenizers and not others. double BOS silently hurts quality, saw it in an eval diff
- chat templates: use the library's apply-template function, don't hand-roll string concat

## roundtrip gotchas
- decode(encode(x)) == x is NOT guaranteed for every tokenizer. some normalize unicode (NFC/NFKC), lowercase, or strip accents
- partial decoding of streamed tokens can produce broken utf-8 mid-character. buffer bytes until valid before printing
- byte-fallback tokens (`<0x E2>` style) show up with rare chars, means the word wasn't in vocab at all

## debugging checklist
1. print the token ids AND the decoded pieces, side by side
2. check for unexpected leading/trailing space tokens
3. confirm special tokens are what I expect, not split into plain text
4. compare against reference tokenizer output on a few tricky strings (unicode, digits, code)
5. verify truncation happens on tokens, not characters

## todo
- write a tiny script that dumps ids + pieces for any string, keep it in snippets
