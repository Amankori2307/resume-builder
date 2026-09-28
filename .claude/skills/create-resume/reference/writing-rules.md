# Bullet writing rules

These are the **global** rules, shipped with the skill and applied to everyone.
Each user can add their own in `meta.json → preferences.rules`; apply those on
top of these, and when the two conflict, the user's rule wins (except rule 5,
which is never overridden).

Apply these when writing or rewriting any bullet. They exist because the
default failure mode of a generated resume is not being wrong — it is being
generic, which is invisible to the writer and obvious to the reader.

## The test for a generic bullet

Delete every adjective from the bullet. If the meaning is unchanged, those
adjectives were filler and must go. Then ask: **could this sentence appear on
someone else's resume unmodified?** If yes, it is describing a job category
rather than the person's actual work.

## Hard rules

1. **No filler adjectives.** Banned unless they carry load a number cannot:
   `comprehensive`, `robust`, `scalable`, `seamless`, `cutting-edge`,
   `state-of-the-art`, `strong`, `successful(ly)`, `various`, `several`,
   `multiple`, `efficient`, `reliable`, `polished`, `complex`.

2. **No repeated words across the document.** Check with:
   ```bash
   grep -o '"text": "[^"]*"' <application dir>/resume.json \
     | tr 'A-Z ' 'a-z\n' | tr -cd 'a-z\n' | sort | uniq -c | sort -rn | head -30
   ```
   If a distinctive word appears three or more times, rewrite all but one.
   Opening verbs especially: no verb should start more than two bullets.

3. **Every bullet needs a mechanism or a number — ideally both.** A mechanism
   is *how* it worked, not that it existed.
   - Generic: `Architected event-driven microservices with comprehensive monitoring`
   - Specific: `Standardized cron and pub/sub task creation behind one task-definition template covering type, message generator, processor and cron config, making new task setup a single-file change`

4. **No placeholder bullets.** A bullet that restates the header
   (`Joined <Company> as <Title> on <date>`) carries zero information in the
   most valuable position on the page. Either write one real thing shipped, or
   leave the role with no bullets.

5. **Never invent anything.** Not a metric, a technology, a title, a team
   size, or a date. If the user hasn't supplied a number, write the mechanism
   and tell them which bullet would be stronger with one. If a claim seems
   likely but isn't stated ("you ran SQS workers, so you've handled
   at-least-once delivery"), **ask** before using it, and save the answer to
   meta. A resume is a factual claim about a real person.

6. **Bold the number, not the sentence.** `**2M events daily**`, not a whole
   bolded clause. Aim for at most one or two bolded spans per bullet.

7. **Do not volunteer weaknesses.** Drop parentheticals like
   `(limited exposure)` or `(basic)` from a skills list. List it or don't.

8. **Self-declared expertise is not evidence.** A skills line reading
   `Expertise: System Design, Performance Optimization` asserts what the
   experience bullets should already demonstrate. Prefer concrete tools and
   let the bullets carry the claim.

## Ordering

Within a role, order bullets by what the target reader values, not
chronologically. The first bullet of the most recent role is the single most
read line — it should be the strongest thing the person has done.

## Length

Aim for one line per bullet in the PDF, two at most. A three-line bullet is
usually two bullets, or one bullet with filler in it.

## Before finishing

Run the repeated-word check above, then re-read the top three bullets and ask
whether a reader could tell this person apart from any other candidate with the
same job title. If not, the resume is generic regardless of how accurate it is.
