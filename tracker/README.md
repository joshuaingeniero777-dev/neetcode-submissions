# Tracker

`tracker.csv` is rebuilt automatically by GitHub Actions every time NeetCode
pushes a submission, plus once a day so the re-solve dates stay current.
Don't edit it by hand, because your changes get overwritten.

## What each column means

| Column | Where it comes from |
|---|---|
| #, Problem, Category, Difficulty | NeetCode 150 roadmap order (`problems.json`) |
| First / Last Solved | Date NeetCode pushed the submission to GitHub |
| Solve Days | Number of separate days you solved it (same-day resubmits count once) |
| Next Re-solve | Spaced repetition: +3 days after day 1, then +7, +14, +30 |
| Status | Not Started, Scheduled, Due Today, Overdue, or Mastered (5 solve days) |
| Needed Help, Key Insight | From an optional notes comment in your code (see below) |

## Adding notes

Put this line anywhere in your solution on NeetCode before you submit:

```python
# help: Y | insight: hashmap of complements
```

`help` is Y or N. For Java, C++, or JS, use `//` instead of `#`.
The newest submission with a notes line wins.

## Excel

1. Excel desktop → **Data → From Web** and paste:
   `https://raw.githubusercontent.com/joshuaingeniero777-dev/neetcode-submissions/main/tracker/tracker.csv`
2. Click **Load**.
3. **Data → Queries & Connections**, right-click the query → **Properties** →
   check **Refresh data when opening the file**.

After that, **Data → Refresh All** pulls in your latest progress. GitHub can
cache the raw file for a few minutes after a push.
