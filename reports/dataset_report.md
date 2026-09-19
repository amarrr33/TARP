# VoxFlow Phase 1: Cleaned Dataset Report (SEP-28k)

**Total Valid Real Stuttering Clips on Disk:** 646
**Quality Filter:** Filtered $\ge 2/3$ consensus, excluded poor audio, music, and multi-label conflicts.

## Speaker-Independent Cohort Distribution

| Split      |   Block |   Fluent |   Prolongation |   Repetition |
|:-----------|--------:|---------:|---------------:|-------------:|
| Test       |      45 |       52 |             43 |           61 |
| Train      |      58 |       71 |            102 |          107 |
| Validation |      11 |       22 |             39 |           35 |

### Speakers per Split (Zero Leakage Verification)
- **Test**: 2 distinct speaker(s): `HeStutters_Ep16, WomenWhoStutter_Ep1`
- **Train**: 3 distinct speaker(s): `HeStutters_Ep1, HeStutters_Ep11, WomenWhoStutter_Ep0`
- **Validation**: 1 distinct speaker(s): `HeStutters_Ep15`

### Verified Leakage Status: **0% Speaker Overlap (Passed)**
