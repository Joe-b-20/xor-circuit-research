# Expected results of `run_all.sh`

Recorded on 2026-10-02 with the corrected runner (version 1.1: no pipe into `tail`; the run stops at the first
failure with a nonzero status; the stress report is validated; `--with-lp` adds the optional LP cross-check).
Full per-script logs go to `logs/` (not tracked). The JSON outputs are written next to the scripts
(`finite_facts.json`, `CHECK72.json`, `CHECK73.json`, `DARK_SOURCE_VERIFIED.json`, `VERIFIED74.json`,
`INDEPENDENT74.json`, `VERIFIED75.json`, `INDEPENDENT75.json`, `stress.json`, and with `--with-lp`
`lp_regen_74.json`). What to look for:

| script | the line that matters |
|---|---|
| finite_facts.py | `ALL FINITE PREMISES RECOMPUTED AND MATCH` (every assertion in the script is a number of the proof note) |
| check72.py | `"minimum_two_step_increment": 3` and positive increments for G = 69, 70, 71 (file CHECK72.json) |
| check73.py | the unique non-positive-drift case a = b = 24, Y = Z = 0, and `"rank": 28` |
| check_dark_source.py | `"rank_R10": 29`, `"complete_nonzero_quotient_word_count": 736`, `"all_checks_passed": true` |
| certify74.py / independent74.py | `"all_checks_passed": true`; 262 states, 524 claims, 484 certificates, largest right side -1 |
| certify75.py / independent75.py | `"all_checks_passed": true`; 1,102 states, 2,204 claims, 4,057 certificates, 9,604 references, 927 direct, largest right side -1 |
| stress.py | `STRESS TEST PASSED` for the 13 circuits of this repository (stress.json has `"failures": []`) |
| the runner | `Stress report accepted` and `ALL CHECKS PASSED`, exit status 0 |
| lp_regen.py (`--with-lp` only) | `LP CROSS-CHECK PASSED`: 0 survivors, 2,204 identical claims, no certified key feasible |

A nonzero exit status, a failed assertion in any script, or a `"failures"` list that is not empty means a
discrepancy with the note and should be reported.

## Transcript (`sh run_all.sh`, standard library)

```

=== finite_facts.py
[   16.5s] Mt: no active six-form label has a two/four form: OK
[   16.5s] Mt: active labels meeting repeated-helper pairs: 632 max pairs per label: 1
[   33.5s] M (u,Mu) nine-part search: words 360 nodes 1485213 leaves 62112 splits found 0
[   34.9s] Mt (u,M^T u) nine-part search: words 308 nodes 91485 leaves 720 splits found 0
[   34.9s] eight-part partition exists (bit families fixed by M): OK
[   34.9s] ALL FINITE PREMISES RECOMPUTED AND MATCH

=== check72.py
          "increment": 5
        }
      ]
    }
  ]
}

=== check73.py
    "triples": 41664,
    "weight_six_relations": 84,
    "rank": 28,
    "zero_missing_zero_helper_edges_implies_y_at_least": 4
  }
}

=== check_dark_source.py
  },
  "rank_R10": 29,
  "complete_nonzero_quotient_word_count": 736,
  "inherited_source_exactly_matches": true,
  "all_checks_passed": true
}

=== certify74.py
    "missing pairs <=",
    "reverse EE budget <=",
    "weighted label capacity <="
  ],
  "all_checks_passed": true
}

=== independent74.py
  "independently_checked_coefficients": 13819,
  "largest_right_side": -1,
  "certificate_references": 1456,
  "distinct_referenced_certificates": 383,
  "all_checks_passed": true
}

=== certify75.py
    "six color packing <=",
    "unanchored required <=",
    "weighted label capacity <="
  ],
  "all_checks_passed": true
}

=== independent75.py
  "largest_right_side": -1,
  "certificate_references": 9604,
  "distinct_referenced_certificates": 3481,
  "direct_geometric_references": 927,
  "all_checks_passed": true
}

=== stress.py
   ],
   1
  ]
 ]
}
STRESS TEST PASSED: 13 circuits, 0 failures
Stress report accepted: 13 circuits, no failures.

ALL CHECKS PASSED (standard-library checks)
```

With `--with-lp` the run additionally prints the last lines of `lp_regen.py` (`LP CROSS-CHECK PASSED: 0 survivors at G=74, all claims identical, no certified key feasible`), then `LP cross-check report matches the expectations`, and ends with `ALL CHECKS PASSED (standard-library checks + LP cross-check)`.
