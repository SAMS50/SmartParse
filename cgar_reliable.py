"""Phase 5E conservative advisor for the experimental whole-program planner.

Grammar validity does not establish author intent. This module preserves
uncertainty instead of inventing identifier names or expression values.
"""
from dataclasses import dataclass
from smartparse import tokenize, Token
from cgar_verified import plan, _strict_error, VerifiedPlan

@dataclass(frozen=True)
class ReliableAdvice:
    status: str  # verified_candidate, ambiguous_valid, unchanged, abstain
    explanation: str
    result: VerifiedPlan | None


def advise(source, *, max_edits=3, max_nodes=150):
    if max_edits < 1 or max_nodes < 1:
        raise ValueError('budgets must be positive')
    tokens = tuple(tokenize(source))
    error = _strict_error(tokens)
    if error is None:
        # Consecutive semicolons are valid empty statements in our grammar.
        # Do not silently remove them merely to match a reference program.
        if any(a.value == b.value == ';' for a, b in zip(tokens, tokens[1:])):
            return ReliableAdvice('ambiguous_valid',
                'Consecutive semicolons are legal empty statements; removal may change intent.', None)
        return ReliableAdvice('unchanged', 'Input already parses under the supported grammar.',
                              plan(source, max_edits=max_edits, max_nodes=max_nodes))

    index, expected = error
    # Narrow, evidence-based repair: declaration `int/float name == expr;`
    # is not valid declaration syntax, while `=` is. This is still a
    # suggestion rather than a proof of author intent.
    if (expected == ';' and tokens[index].value == '==' and index >= 2
        and tokens[index-1].kind == 'ID'
        and tokens[index-2].value in ('int', 'float')):
        bad = tokens[index]
        fixed = tokens[:index] + (Token('=', '=', bad.line, bad.col),) + tokens[index+1:]
        if _strict_error(fixed) is None:
            result = VerifiedPlan((('substitute', index, '==->='),), fixed, 1, 'grammar_valid')
            return ReliableAdvice('verified_candidate',
                'Declaration expects an initializer operator; replacing == with = parses.', result)

    result = plan(source, max_edits=max_edits, max_nodes=max_nodes)
    if result is None:
        return ReliableAdvice('abstain',
            'No safe grammar-verified repair found within the search budget; no value was guessed.', None)
    return ReliableAdvice('verified_candidate',
        'Candidate passes strict grammar validation; programmer intent remains unverified.', result)
