## What I Unlearned While Building Stall Alerter

## 1. Rethinking My Approach to Coding

One of the biggest things I unlearned while building Stall Alerter was my habit of moving straight into coding once I understood the problem.

- Previously, I spent very little time developing detailed prompts because I wanted to start implementation quickly.
- I thought writing code early meant making progress, but I realised that a better-defined prompt could help me generate the right implementation much faster.
- The tight deadline for this task forced me to reconsider that approach.

## 2. Understanding the Problem Before Implementation

Instead of rushing into implementation, I invested more time in understanding the problem, identifying who the product was intended to help, and thinking through how recruiters would actually use it.

This led me to consider:

- The differences between companies and their recruitment processes.
- The need for each company to configure its own hiring stages, stage deadlines, weights, and recommended actions.
- How to prioritise candidates based on follow-up urgency.

I also reconsidered the initial scoring formula rather than accepting it without question.

- I rejected an approach that combined candidate assessment performance with follow-up urgency.
- I wanted the application to identify who needed attention first without allowing assessment scores to distort that decision.

## 3. Using AI With Clear Direction

Once I had worked through the product requirements, I gave the LLM my product decisions and asked it to help develop a detailed implementation prompt.

The prompt covered:

- Architecture and folder structure.
- Required files and their responsibilities.
- Expected application behaviour.
- Validation rules and edge cases.
- Test cases and expected outcomes.

I also structured the work so that the implementation could be evaluated against clear requirements.

The result was a working implementation with a test suite that gave me a much stronger starting point than writing everything incrementally myself would have.

- Estimated time saved: Based on my experience on this task, I estimate that this approach reduced my implementation time by around 80%.
- Measurement note: This is my personal estimate, not a formally timed measurement.

## 4. Learning That AI Does Not Replace Verification

Although AI accelerated implementation, the remaining engineering work was still important.

I had to:

- Test the implementation.
- Inspect the results.
- Identify issues and unexpected behaviour.
- Refine requirements and prompts.
- Iterate with the LLM until the application behaved more closely to what I intended.

This changed how I think about productivity as an engineer. Moving straight into coding is not always the fastest way to deliver. Spending more time thinking, researching, and defining the task before implementation can save much more time later.

I also learned that a good prompt does not guarantee good software. Testing, debugging, and refinement remain my responsibility.

## 5. Building Confidence With Unfamiliar Tools

Another unexpected outcome was the confidence this project gave me to work with an unfamiliar tool.

- I had never used Streamlit before this project.
- I was able to get a working interface running in less than an hour.
- I then improved it through testing and further prompts.

This experience reminded me that my existing knowledge of clean architecture, programming principles, and software development is transferable.

- I do not have to know every tool in advance before attempting to build something useful.
- I can learn what I need, use AI to accelerate that learning, and apply my engineering knowledge to evaluate the result.

## 6. What I Will Carry Forward

The biggest lesson I took from Stall Alerter is that effective AI-assisted engineering begins before code generation.

It begins with understanding the problem, making deliberate product decisions, and communicating those decisions clearly enough for AI to help implement them.

I have not concluded that coding is less important or that a good prompt guarantees good software. Rather, I have learned to invest more thought in the work that comes before coding and use the time saved for testing, debugging, and refinement.

Going forward, I want to apply this approach to my engineering work:

1. Understand the problem before implementation.
2. Define the expected outcome and requirements.
3. Prepare a structured, detailed prompt.
4. Use AI to accelerate implementation.
5. Test the result, debug issues, and refine the solution.
6. Take responsibility for verifying what gets built.

---

Key takeaway: Effective AI-assisted engineering is not just about generating code faster. It is about thinking clearly, making deliberate decisions, directing AI effectively, and taking responsibility for the quality of the final software.
