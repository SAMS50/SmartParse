# Milestone 14 root-cause analysis

Completed before implementing the adaptive algorithm. Reproduced frozen v13 final results: 79 primary A cases; existing scoring 20 exact, 4 exact mismatches, 55 abstentions; full scoring 79 abstentions. One additional B case is excluded consistently. This split was exposed in v13 and is historical, not an unseen evaluation set.

45 pools contain no generated program; 10 contain generated but rejected programs; 24 contain one validated program. All 24 validated inputs retain preprocessing and have seven UNKNOWN historical semantic checks; no preceding histories exist. Full mode confuses unsupported/unavailable structural evidence with a mandatory recommendation gate. No verified structural change was found in these valid pools.

A lower-assurance syntax fallback is possible on those 24, but compiler acceptance alone does not prove intent: four existing recommendations mismatch the reference (one is token-equivalent). There is no numeric-ranking solution to 55 pools with no valid candidate. Custom lexing rejects common real-C headers/types; supplemental search rejects preprocessing wholesale. Clang hints already enter v12 generation but attribution is only an origin string, not a separately evaluated provider.

The general changes justified by this diagnosis are explicit evidence availability/risk states, a conservative syntax-only policy, source-mapped compiler candidate bundles, and separate custom/compiler/combined pools. Do not whitelist the twenty known successes or blacklist the four known mismatches. Calibrate only on the v13 development split and test on new family-disjoint cases; label this original split exposed.

## Complete primary-case ledger

| Case | Error category | Generated / valid | Intended available | Syntax/compiler validation | Independent compiler check | History | Semantic availability | Abstention reason | Theoretical fallback |
|---|---|---:|---|---|---|---|---|---|---|
| 3db39a1a10f4cd0a5e6d42f3 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| a9ae9aea789b39a45a1fe1ae | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 2ae2817d0b8a70863745dce9 | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 1a09ec4a316d51ab072d0670 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| d19bdbff34dbbd4c6d1f6535 | name/type | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 5fd70bfa770da54050ed5658 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| b68a717b0bb663662a524b74 | type/expression | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| f8adeceeb45f269d553954d5 | type/expression | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| dd415587480a949de22a2201 | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 804a5018996dbc96bd757eee | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| dabe1d75f3dc3df9883dd10e | syntax/delimiter | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| ab866d4b308fe719c2312dac | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 52d9fe82e6a48de77dfb49e0 | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 9fce7ec31171e0412e70f07e | name/type | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 295215b1636198187a1cf8ad | type/expression | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 331173652ceab2f23f8c517f | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| da68feed9bc319e6a2475a1f | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| f633f80ea3d4d21bd3609437 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| b03e862de257e5ff77011979 | type/expression | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 56a96d003cf6b3c2cd7a6edd | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 24c4def1f11aab4b4e84978f | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 6f67a55a4667f474d6f1d001 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| d0500ad7effa4f3c6ed37af2 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| e094eb7ece6f3e912a077025 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 650263c77dead603bfefe339 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 01e950795bb3e2f440ed622f | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 6b1e808b14c53edc1fe4dca6 | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| d43660c3da53eade75ad5fca | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 3a49b8cd3127bac31f6fb79f | syntax/delimiter | 1 / 1 | False | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 73f19c15332ac1eaa4daa977 | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 1384ba97be222abf9aecd974 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| c51fab3abde843bad8c9e954 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 3352f6a69169c82fa6c1ea4a | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 2acba2c49b40982aaea415c2 | name/type | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| baac60b36d43bc0a34566abc | syntax/delimiter | 1 / 1 | False | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| d7c5cb24a4f3de56df4e33cf | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 5efa83ff4c832b62b945253e | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 1a42840481a61092778b449c | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 6aefeeb5263ae69d8bb6f6ba | other | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| d41d4f6212bcf1486c79edf6 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 15da60b7b649d3c4d511cb9a | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 7c574c4767902ed40e9da9a6 | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| c9468ffe90cc6731c4d1320f | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 0ded616efdc6a53ab7c692c2 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| b4c008aa112507a3983226ca | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 9ebf768e96fac12afcc679b2 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| edae0a568771c85fb2f01e01 | syntax/delimiter | 4 / 0 | False | {'INVALID': 4} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 73bebc8e733f3707d0a3dc3b | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 41358c2c9f600d64fd22aeaf | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 0befd7cf976216349383b318 | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 6b97566afe5ac92773310e6c | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 8868f10a24286eeb2a71de63 | type/expression | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 47797a644243746ffaf3cc2b | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| d4486d76e11cc74cacd91ed3 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 8bf730761a0949ad5df97dbd | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 0dce2b05da61927d8e2784a1 | syntax/delimiter | 7 / 0 | False | {'INVALID': 7} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| c0c41e25b601c52f9ca9c869 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| d57c3fc5b8bec3c1b9abd002 | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 9b50ae98a27dcf39936cdb87 | name/type | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| a37cee98aec81cb9c4e3d018 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| a4bb70e0d77b8dbd3bcf6653 | syntax/delimiter | 1 / 1 | False | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| f2ce1851dd1c844189e7181d | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| dcdf5402328d1f69d6625567 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| a125cabd7fefd3f8dbb95abc | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| fa20df242731979f9f8b26e5 | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| d0c8e27867f77176cdb1bd35 | syntax/delimiter | 1 / 1 | False | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 5264170c8d5c8f1773844c2a | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 4373b47d4eb18c50e0d0cd75 | syntax/delimiter | 2 / 0 | False | {'INVALID': 2} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| e51dc0cca80e59f5c0c213f7 | syntax/delimiter | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| f179c4f09259453fa64ff9ea | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| d8b1d398ff37fd25843f5d31 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 3729d17d385c3743a733dfeb | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 10177366787df54c8ccc1b65 | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 09f193cee0c8848765798a8d | name/type | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| bb96ef5455f26c985f1abc7b | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 1ffaad3e56ba9e260f66d4ff | syntax/delimiter | 1 / 1 | True | {'VALID': 1} | {'gcc': True, 'clang': True} | none | UNKNOWN (preprocessing unsupported) | The behavioral impact could not be determined. | Lower-assurance compiler-valid syntax fallback possible; intent not proved |
| 08a5bacebc1effbb29e3f68d | syntax/delimiter | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 3ecce859eacc822892d77e6e | syntax/delimiter | 1 / 0 | False | {'INVALID': 1} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |
| 526a5a4984c6157c9e9ccc11 | other | 0 / 0 | False | {} | None | none | no valid AST | No candidate satisfies syntax validation | No validated candidate; ranking fallback cannot supply one |

Candidate IDs, origins, score, validation statuses, exact edit locations/lengths and all seven semantic statuses are in `results/root-causes.json`. Student code remains local, not redistributed.

## Existing exact successes (20)

`1a09ec4a316d51ab072d0670`, `5fd70bfa770da54050ed5658`, `ab866d4b308fe719c2312dac`, `331173652ceab2f23f8c517f`, `f633f80ea3d4d21bd3609437`, `650263c77dead603bfefe339`, `c51fab3abde843bad8c9e954`, `2acba2c49b40982aaea415c2`, `d7c5cb24a4f3de56df4e33cf`, `6aefeeb5263ae69d8bb6f6ba`, `d41d4f6212bcf1486c79edf6`, `b4c008aa112507a3983226ca`, `6b97566afe5ac92773310e6c`, `47797a644243746ffaf3cc2b`, `d4486d76e11cc74cacd91ed3`, `f2ce1851dd1c844189e7181d`, `dcdf5402328d1f69d6625567`, `a125cabd7fefd3f8dbb95abc`, `fa20df242731979f9f8b26e5`, `1ffaad3e56ba9e260f66d4ff`

## Existing exact mismatches (4)

`3a49b8cd3127bac31f6fb79f`, `baac60b36d43bc0a34566abc`, `a4bb70e0d77b8dbd3bcf6653`, `d0c8e27867f77176cdb1bd35`

An exact mismatch is not a proven behavioral change. The full policy avoided these four only by withholding twenty exact successes as well. Missing history is unavailable evidence, not evidence against every candidate. Unsupported semantic projection is not a detected structural hazard.
