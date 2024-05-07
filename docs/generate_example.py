"""Simple script to generate example synthetic voting data."""

import csv

import numpy as np

rng = np.random.default_rng(42)

# question -> (num_rankings, answer -> weight)
data = {
    "Rank your 4 favorite pizza toppings (3 winners)": (
        4,
        {
            "Pepperoni": 100,
            "Sausage": 80,
            "Bell Peppers": 50,
            "Onions": 40,
            "Ground Beef": 50,
            "Olives": 20,
            "Mushrooms": 60,
            "BBQ Chicken": 40,
            "Pineapple": 60,
            "Basil": 30,
            "Chorizo": 80,
        },
    ),
    "Rank the seasons": (4, {"Summer": 100, "Autumn": 50, "Winter": 20, "Spring": 50}),
}


def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


with open("example_election.csv", "w") as outfile:
    writer = csv.writer(outfile)

    header = []
    for question, (_, answers) in data.items():
        header.extend([f"{question} [{answer}]" for answer in answers])
    writer.writerow(header)

    for idx in range(250):
        row = []
        for _, (num, answers) in data.items():
            num_answers = len(answers)
            response = [""] * num_answers
            prob = np.array(list(answers.values())).astype(float)
            prob /= prob.sum()
            indices = rng.choice(range(num_answers), size=num, replace=False, p=prob)
            for rank, index in enumerate(indices):
                response[index] = ordinal(rank + 1)
            row.extend(response)
        writer.writerow(row)
