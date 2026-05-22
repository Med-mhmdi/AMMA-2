# AMMA Recommendation System Report

## 1. RecSys Concept for AMMA

AMMA does not recommend products. It recommends financial actions. The goal is to help users reduce unnecessary spending, avoid budget overruns, repay loans on time, and improve financial habits.

Examples of recommendations:

- Reduce food spending by 10% next month.
- Set a weekly limit for entertainment expenses.
- Pay back a loan before the return date.
- Avoid non-essential spending because the monthly budget usage is above 90%.
- Increase savings if income is stable and expenses are below budget.

## 2. Approach 1: Content-Based Recommendation

A content-based recommender uses the user's own financial profile.

Input features:

- Monthly income
- Expense categories
- Spending frequency
- Budget usage percentage
- Loan status
- Historical balance
- Preferred categories

Example rule:

If the user spends more than 40% of monthly expenses on food, recommend reducing food spending or creating a food category budget.

Strength:

- Works with one user's data.
- Good for personal finance.
- Does not require many users.

Weakness:

- Recommendations can become repetitive.
- Cold start still exists if the user has no financial history.

## 3. Approach 2: Collaborative Filtering

A collaborative recommender compares users with similar financial behavior.

Similarity can be based on:

- Income range
- Expense distribution
- Budget overrun pattern
- Loan behavior
- Saving behavior

Example:

Users with similar spending patterns reduced entertainment expenses by using weekly limits. AMMA can recommend the same strategy to a similar user.

Strength:

- Can discover patterns not visible from one user alone.
- Useful when the system has many users.

Weakness:

- Needs enough user data.
- Privacy must be protected.
- Cold start is stronger than content-based filtering.

## 4. Approach 3: Heuristic Baseline

A heuristic baseline is simple, explainable, and useful even before enough data exists.

Rules:

| Condition | Recommendation |
|---|---|
| Budget usage > 90% | Warn the user and recommend reducing non-essential spending |
| Spending in one category increases by 30% | Recommend category limit |
| Loan return date is close | Send repayment reminder |
| Balance is negative | Recommend stopping optional expenses |
| Monthly income is stable and expenses are low | Recommend increasing savings |

Strength:

- Easy to implement.
- Easy to explain in defense.
- Works without ML.

Weakness:

- Less personalized.
- Rules must be maintained manually.

## 5. Production Problems and Solutions

### Cold Start

Problem: new users have little or no transaction history.

Solution: use a short onboarding survey and heuristic recommendations.

Shortcoming: too many questions can increase early user churn.

### Ethical Issues

Problem: financial recommendations can affect user behavior in sensitive ways.

Solution: keep recommendations explainable and avoid aggressive financial advice.

Shortcoming: safer recommendations may be less powerful.

### Slow Response Time

Problem: analytics and recommendations may be slow if calculated on every request.

Solution: use Redis cache and precomputed snapshots.

Shortcoming: cache invalidation must be correct.

### Privacy

Problem: financial data is sensitive.

Solution: separate databases per service, JWT authentication, and anonymized collaborative filtering.

Shortcoming: anonymization can reduce model accuracy.

## 6. Evaluation Metrics

ML metrics:

- Precision@K
- Recall@K
- NDCG@K
- MAP

Business metrics:

- Budget overrun reduction
- Saving rate improvement
- Recommendation acceptance rate
- Loan delay reduction
- Monthly active users
- Retention

Production metrics:

- Recommendation latency
- Redis cache hit rate
- Kafka consumer lag
- Failed recommendation rate
- LLM cost per recommendation

## 7. Integration with AMMA

The recommendation logic can be placed inside the Multi-Agent Service as `RecommendationAgent` or later extracted into a separate Recommendation Service. Kafka topics such as `expense.created`, `budget.updated`, and `analytics.snapshot.created` provide the data stream for generating recommendations.
