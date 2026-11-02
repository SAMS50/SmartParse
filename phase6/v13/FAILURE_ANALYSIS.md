# Real-world failure analysis

Final primary set: 79 A cases. 45 have an empty generated pool; 10 generate programs but none validates; 24 have one validated program with seven UNKNOWN semantic checks. Full mode abstains on all. No candidate-budget truncation is reported. This does not imply exhaustive coverage: generation is deliberately restricted to existing rules/fix-its and bounded supplements.

## Root causes

* All 24 validated pools retain preprocessing directives. The frozen semantic projection rejects preprocessing before claiming preservation; history is also missing. These are unsupported-analysis abstentions, not proven safety failures.
* Candidate coverage is only 20/79 exact intended programs. Header-bearing full C bypasses much of the custom lexer/grammar search, and identifier/type, expression and multi-diagnostic errors often lack applicable complete fixes.
* Four existing-score outputs compile but differ from intended text: `3a49b8cd3127bac31f6fb79f`, `baac60b36d43bc0a34566abc`, `a4bb70e0d77b8dbd3bcf6653`, `d0c8e27867f77176cdb1bd35`. The second is token-equivalent; the others differ in tokens. No behavioral oracle justifies calling them semantically wrong/equivalent.
* Valid pools are singletons, so changing relative ranking or margin cannot supply missing evidence. The full policy avoids four exact mismatches by withholding twenty correct repairs too. This is not useful coverage-preserving error reduction.
* Final case `c23cde4be2a55ede8b3da081` is category B: both installed compilers reject its target. Its intended-repair label remains locally unverified and is excluded from primary accuracy, with no replacement case.
* Clang machine hints sometimes address only some errors: twelve of its 36 applicable bundles still fail compilation. GCC 6.3 lacks the probed machine-edit flag; source rejection remains measured separately.
* Real-history contribution is unidentifiable; constructing edits from future corrected endpoints would artificially favor SmartParse and was forbidden. No post-final algorithm changes were made.

## Complete final case ledger

| Case hash | Class | Error category | Lines | Error diagnostics | Valid candidates | Intended generated | Existing exact / token | Full reason |
|---|---|---|---:|---:|---:|---|---|---|
| 3db39a1a10f4cd0a5e6d42f3 | A | syntax/delimiter | 19 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| a9ae9aea789b39a45a1fe1ae | A | other | 12 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 2ae2817d0b8a70863745dce9 | A | other | 10 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 1a09ec4a316d51ab072d0670 | A | syntax/delimiter | 18 | 2 | 1 | True | True / True | The behavioral impact could not be determined. |
| d19bdbff34dbbd4c6d1f6535 | A | name/type | 40 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 5fd70bfa770da54050ed5658 | A | syntax/delimiter | 37 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| b68a717b0bb663662a524b74 | A | type/expression | 29 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| f8adeceeb45f269d553954d5 | A | type/expression | 7 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| dd415587480a949de22a2201 | A | name/type | 21 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 804a5018996dbc96bd757eee | A | name/type | 51 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| dabe1d75f3dc3df9883dd10e | A | syntax/delimiter | 43 | 3 | 0 | False | False / False | No candidate satisfies syntax validation |
| ab866d4b308fe719c2312dac | A | syntax/delimiter | 9 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 52d9fe82e6a48de77dfb49e0 | A | other | 39 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 9fce7ec31171e0412e70f07e | A | name/type | 12 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 295215b1636198187a1cf8ad | A | type/expression | 25 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 331173652ceab2f23f8c517f | A | syntax/delimiter | 22 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| da68feed9bc319e6a2475a1f | A | syntax/delimiter | 18 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| c23cde4be2a55ede8b3da081 | B | other | 41 | 3 | 0 | False | False / False | No candidate satisfies syntax validation |
| f633f80ea3d4d21bd3609437 | A | syntax/delimiter | 41 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| b03e862de257e5ff77011979 | A | type/expression | 34 | 3 | 0 | False | False / False | No candidate satisfies syntax validation |
| 56a96d003cf6b3c2cd7a6edd | A | name/type | 16 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 24c4def1f11aab4b4e84978f | A | syntax/delimiter | 73 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 6f67a55a4667f474d6f1d001 | A | syntax/delimiter | 25 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| d0500ad7effa4f3c6ed37af2 | A | syntax/delimiter | 19 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| e094eb7ece6f3e912a077025 | A | syntax/delimiter | 17 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 650263c77dead603bfefe339 | A | syntax/delimiter | 73 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 01e950795bb3e2f440ed622f | A | syntax/delimiter | 30 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 6b1e808b14c53edc1fe4dca6 | A | other | 34 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| d43660c3da53eade75ad5fca | A | syntax/delimiter | 12 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 3a49b8cd3127bac31f6fb79f | A | syntax/delimiter | 30 | 1 | 1 | False | False / False | The behavioral impact could not be determined. |
| 73f19c15332ac1eaa4daa977 | A | other | 28 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 1384ba97be222abf9aecd974 | A | syntax/delimiter | 23 | 7 | 0 | False | False / False | No candidate satisfies syntax validation |
| c51fab3abde843bad8c9e954 | A | syntax/delimiter | 20 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 3352f6a69169c82fa6c1ea4a | A | syntax/delimiter | 53 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 2acba2c49b40982aaea415c2 | A | name/type | 65 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| baac60b36d43bc0a34566abc | A | syntax/delimiter | 35 | 1 | 1 | False | False / True | The behavioral impact could not be determined. |
| d7c5cb24a4f3de56df4e33cf | A | syntax/delimiter | 20 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 5efa83ff4c832b62b945253e | A | syntax/delimiter | 14 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 1a42840481a61092778b449c | A | other | 76 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 6aefeeb5263ae69d8bb6f6ba | A | other | 45 | 2 | 1 | True | True / True | The behavioral impact could not be determined. |
| d41d4f6212bcf1486c79edf6 | A | syntax/delimiter | 33 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 15da60b7b649d3c4d511cb9a | A | syntax/delimiter | 26 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 7c574c4767902ed40e9da9a6 | A | name/type | 53 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| c9468ffe90cc6731c4d1320f | A | syntax/delimiter | 87 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 0ded616efdc6a53ab7c692c2 | A | syntax/delimiter | 17 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| b4c008aa112507a3983226ca | A | syntax/delimiter | 144 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 9ebf768e96fac12afcc679b2 | A | syntax/delimiter | 38 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| edae0a568771c85fb2f01e01 | A | syntax/delimiter | 19 | 13 | 0 | False | False / False | No candidate satisfies syntax validation |
| 73bebc8e733f3707d0a3dc3b | A | name/type | 38 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 41358c2c9f600d64fd22aeaf | A | name/type | 62 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 0befd7cf976216349383b318 | A | name/type | 21 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 6b97566afe5ac92773310e6c | A | syntax/delimiter | 19 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 8868f10a24286eeb2a71de63 | A | type/expression | 30 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 47797a644243746ffaf3cc2b | A | syntax/delimiter | 30 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| d4486d76e11cc74cacd91ed3 | A | syntax/delimiter | 33 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 8bf730761a0949ad5df97dbd | A | syntax/delimiter | 37 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 0dce2b05da61927d8e2784a1 | A | syntax/delimiter | 75 | 48 | 0 | False | False / False | No candidate satisfies syntax validation |
| c0c41e25b601c52f9ca9c869 | A | syntax/delimiter | 20 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| d57c3fc5b8bec3c1b9abd002 | A | name/type | 19 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |
| 9b50ae98a27dcf39936cdb87 | A | name/type | 15 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| a37cee98aec81cb9c4e3d018 | A | syntax/delimiter | 35 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| a4bb70e0d77b8dbd3bcf6653 | A | syntax/delimiter | 11 | 1 | 1 | False | False / False | The behavioral impact could not be determined. |
| f2ce1851dd1c844189e7181d | A | syntax/delimiter | 28 | 2 | 1 | True | True / True | The behavioral impact could not be determined. |
| dcdf5402328d1f69d6625567 | A | syntax/delimiter | 24 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| a125cabd7fefd3f8dbb95abc | A | syntax/delimiter | 20 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| fa20df242731979f9f8b26e5 | A | syntax/delimiter | 73 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| d0c8e27867f77176cdb1bd35 | A | syntax/delimiter | 31 | 1 | 1 | False | False / False | The behavioral impact could not be determined. |
| 5264170c8d5c8f1773844c2a | A | syntax/delimiter | 20 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 4373b47d4eb18c50e0d0cd75 | A | syntax/delimiter | 22 | 6 | 0 | False | False / False | No candidate satisfies syntax validation |
| e51dc0cca80e59f5c0c213f7 | A | syntax/delimiter | 11 | 3 | 0 | False | False / False | No candidate satisfies syntax validation |
| f179c4f09259453fa64ff9ea | A | syntax/delimiter | 64 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| d8b1d398ff37fd25843f5d31 | A | syntax/delimiter | 38 | 3 | 0 | False | False / False | No candidate satisfies syntax validation |
| 3729d17d385c3743a733dfeb | A | syntax/delimiter | 31 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 10177366787df54c8ccc1b65 | A | syntax/delimiter | 15 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 09f193cee0c8848765798a8d | A | name/type | 28 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| bb96ef5455f26c985f1abc7b | A | syntax/delimiter | 17 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 1ffaad3e56ba9e260f66d4ff | A | syntax/delimiter | 28 | 1 | 1 | True | True / True | The behavioral impact could not be determined. |
| 08a5bacebc1effbb29e3f68d | A | syntax/delimiter | 14 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 3ecce859eacc822892d77e6e | A | syntax/delimiter | 38 | 2 | 0 | False | False / False | No candidate satisfies syntax validation |
| 526a5a4984c6157c9e9ccc11 | A | other | 46 | 1 | 0 | False | False / False | No candidate satisfies syntax validation |

Cases are identified by source-derived hashes and frozen CSV ordinals, not student identifiers. No source snippets are reproduced. Error categories are diagnostic heuristics and reported counts can include cascades. This sample is insufficient to classify all remaining failures as programmer-intent ambiguity; many are simply outside supported generation/analysis.
