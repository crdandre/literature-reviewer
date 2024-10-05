import controlflow as cf


emails = [
    "Hello, I need an update on the project status.",
    "Subject: Exclusive offer just for you!",
    "Urgent: Project deadline moved up by one week.",
]

# Create agents
classifier = cf.Agent(
    name="Email Classifier",
    model="openai/gpt-4o-mini",
    instructions="You are an expert at quickly classifying emails. Always "
                 "respond with exactly one word: either 'important' or 'spam'."
)

responder = cf.Agent(
    name="Email Responder",
    model="openai/gpt-4o",
    instructions="You are an expert at crafting professional email responses. "
                 "Your replies should be concise but friendly."
)


# Create the flow
@cf.flow
def process_email(email_content: str):

    # Classify the email
    category = cf.run(
        f"Classify this email",
        result_type=["important", "spam"],
        agents=[classifier],
        context=dict(email=email_content),
    )

    # If the email is important, write a response
    if category == "important":
        response = cf.run(
            f"Write a response to this important email",
            result_type=str,
            agents=[responder],
            context=dict(email=email_content),
        )
        return response

    # Otherwise, no response is needed
    else:
        print("No response needed for spam email.")


# Run the flow on each email
for email in emails:
    response = process_email(email)
    print(response)