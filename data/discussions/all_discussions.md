# AIMO3 Competition Discussions

Scraped: 2026-03-02 | Total: 20 threads | 118 comments | 71 linked URLs

---

## Public vs Private problem set difficulty comparison
**ID:** 679559 | **Author:** Simon Frieder | **Date:** 2026-03-02 | **Comments:** 3

### Reply 1 — N/A (2026-03-02)

I was about to guess the two models are gpt-oss-20b and gpt-oss-120b, but I have some doubts.

It seems that gpt-oss-120b could not even score 32 with pass@5 without tool calling.

These are I think the differences with the leaderboard submissions
- Tool calling is allowed in submissions
- Your submission is unlikely to run the full context length for all submissions
- You can only submit only one answer, whereas pass@100 means it is considered correct if any of the 100 submission is correct

### Reply 2 — N/A (2026-03-02)

@friederrr 
I have 3 questions. 

1) There was no time constraints for any of the experiments shown above ? 
I mean, the model was run in full context, max output tokens mode with unlimited budget? And of course this is in pov that individual pass @ n were not carried out but extrapolated from pass @ 100 ?

2) Also when you mentioned that no optimizations were carried, does that also align with respect to the sampling parameters used during inference like temperature, min and top P ? Were the default ones used?

3) ```and we used bootstrapping```. During bootstrapping and picking samples, were duplicates/ re sampling discarded for getting scores (to reduce noise) for other pass @ n scores? 

And can you reveal any spoilers on if the same model families were used 😉
PS: just kidding :D

### Reply 3 — N/A (2026-03-02)

If nearly all problems can be solved at pass@100 without finetuning or tool calling, does this mean that this year’s competition is primarily measuring true model reasoning capability, or rather the ability to control randomness and reduce variance?

In that context, could final results be influenced too heavily by stochastic effects?

And if so, does the prize ultimately reflect the core capability the competition aims to evaluate, or something more related to engineering robustness and variance management?

---

## B200 + calls bug fix
**ID:** 672978 | **Author:** Simon Frieder | **Date:** 2026-02-11 | **Comments:** 2

### Reply 1 — N/A (2026-02-11)

For a moment I thought we now have access to B200 on Kaggle, but it is not the case.

In my experience Triton backend is slower, but I have not seriously benchmarked it (probably I could have written a benchmarking notebook)

### Reply 2 — N/A (2026-02-19)

great learning from this content

---

## Finetuning a model with just a handful of parameters
**ID:** 672594 | **Author:** Simon Frieder | **Date:** 2026-02-09 | **Comments:** 2

**Linked URLs:** https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672611

### Reply 1 — N/A (2026-02-10)

I wonder if any work has been done on the extra requirements of a dataset when it's a MoE vs a dense model -- in particular because MoE routing adds an extra failure point.  

In particular, I'm concerned if their previous training under MoE teaches a "latent variable regime" that must be present for future data to be effective.   Or, is my concern is completely baseless -- I guess, my question is :
"When you use train a MoE model, is there any extra considerations you must enforce on your data to make sure that routing doesn't collapse outside of your training data?" 

### Reply 2 — N/A (2026-02-09)

I HAVE LORA WITH 4408 STEPS AT [HERE](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672611)

---

## AIMO2 LLM Reasoning Long List pointers
**ID:** 672384 | **Author:** Simon Frieder | **Date:** 2026-02-07 | **Comments:** 2

### Reply 1 — N/A (2026-02-08)

i know this isnt the thread for this question but, could u plz clarify whether we’ll be receiving tinker credits or not??

### Reply 2 — N/A (2026-02-09)

Nice Information

---

## Math Corpus Prize -- final considerations 
**ID:** 671893 | **Author:** Simon Frieder | **Date:** 2026-02-04 | **Comments:** 5

### Reply 1 — N/A (2026-02-08)

Do you expect/accept  Mathematics question related to Mechanics & Statistics (e.g. Forces and equilibrium, Momentum, Kinematics, Newton’s laws of motion, Permutations and combinations, normal distribution, Discrete random variables, Poisson distribution, Hypothesis tests etc) that is Mathematics in nature but not really in the area of Pure Mathematics ?

### Reply 2 — N/A (2026-02-08)

The goal post is a little ephemeral ; is the metric "Is useful for the competition" or "The community thinks it's useful for the competition"?

They seem to be distinct here.

### Reply 3 — N/A (2026-02-06)

Is it Latex mandatory for all the equation in the dataset?

For example if the original questions are in Microsoft Word in OMML or UnicodeMath (which display standard human readable equation without Latex  that I consolidated into a dataset usable for Machine Learning task, do I need to convert it to Latex syntax ?

### Reply 4 — N/A (2026-02-06)



### Reply 5 — N/A (2026-02-05)



---

## The Math Corpus Prize and LL Prize are ending soon! Prepare your submissions!
**ID:** 670047 | **Author:** Simon Frieder | **Date:** 2026-01-25 | **Comments:** 7

**Linked URLs:** https://www.kaggle.com/datasets/sangrampatil5150/math-corpus-grpo-2-6k-dataset/data/data/data, https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671107

### Reply 1 — N/A (2026-02-09)

## Math Corpus Prize — Activation Aware Fusion

- **Method overview / discussion:**  
  www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672575

- **Dataset:**  
www.kaggle.com/datasets/aneeshmukkamala/aimo3afq

### Reply 2 — N/A (2026-02-04)

Will I be free to use other's dataset from here to finetune my own model? 

Does the dataset have to be strictly math entries only? 
     We propose this question because teaching math doesn't always mean teaching math problems. Teaching how to ask questions also directly influences how the student, in this case the model, learns how to solve problems. Knowing/learning how to ask the right questions is important to solve a problem. 

 You mention 400 sufficiently original problems+solutions can be a good contender. 
    This is a separate intepretation of `corpus`. For math purposes, this is good. This style of submission suggests non-math entries should not belong to the final submission. 


I am conflicted because I was building a corpus that teaches math to a model during finetune. I finished turning bhagavad gita and bible into a dataset that has all together ~40k entries. Next stops were tripitaka, dao, vedas, zoroastranism. I was thinking appolonius' texts, pythagorean texts, plato, socrates, aristotalean dialogues. Texts from available books of davinci, archimedes, newton, russell, cantor, riemann, al jabr, all medieval algebra texts found from the meditarrenean, quine, turing, babbage, ada, and a few more. With that spirit I was about to collect/synthesize math problems from grade 1 to grade 12 of all countries that taught math, translate them in english and teach the model math, so they will have reasoning skills from a lot of different countries, especially the resources from the competitive countries for imo. All of these I suspect to be around ~200k entries, if dug properly. 
Then I was running into licensing problems, because I don't know if I can simply release someone else's book content to kaggle/huggingface. Even if I reinterpreted it in my own language, I don't know if that is ethical/within CC BY 4 or any opensourcing grounds. Its going to be really hard to really find mathematical gems if all we rely is open sourced data found in web. 
A separate case is when there is no digital data available of a certain book, converting that into a dataset is perfect. And I would definitely train it to `my` model, and would benefit everyone as well. 

Given the number of days remaining 400 sufficiently original problems is also a path that can be taken. This will make me completely change my current dataset building schema, but it is very achievable. 


All my points raised about a math-corpus to include more than just math problems still stands. 

Thank you for reading. 


### Reply 3 — N/A (2026-02-01)

Edit: Reposting in the other discussion as requested

### Reply 4 — N/A (2026-01-31)

I am entering my dataset for the Math Corpus Prize.

Dataset Name: Math Corpus GRPO Dataset

Dataset Link: [Link](https://www.kaggle.com/datasets/sangrampatil5150/math-corpus-grpo-2-6k-dataset/data/data/data)

Detailed Write-up: [Link](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671107)

### Reply 5 — N/A (2026-01-26)



### Reply 6 — N/A (2026-01-26)



### Reply 7 — N/A (2026-01-25)



---

## Test Data Update and Rescore
**ID:** 669690 | **Author:** Ryan Holbrook | **Date:** 2026-01-23 | **Comments:** 7

**Linked URLs:** https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/submissions, https://www.kaggle.com/nadinesquires, https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F1680925%2F6b1a48a4086f358307b8eae0d4752712%2FScreenshot%202026-01-23%20at%2017.20.09.png?generation=1769217623309243&alt=media

### Reply 1 — N/A (2026-01-23)

Here is our own announcement around this issue: In the interests of transparency, we want to notify the community that through our secondary review process, errors were found in two problems from the public leaderboard that require correction.     

Problem A: Incorrect answer. Kaggle will rescore all existing submissions using the corrected answer. This will be reflected in the leaderboard and the calculation for the Longest Leader Prize.
            

Problem B: The problem statement requested an answer in a format that is not valid for the actual solution. The problem statement has been corrected and the requested answer format updated. Submissions will be evaluated against the updated version.            


As these two problems are comparatively quite hard (for humans and LLMs), very few teams submitted correct answers to either problem, so we expect minimal impact on standings.

— The AIMO Team

### Reply 2 — N/A (2026-01-25)

Hi Ryan,

I’m reaching out because I’ve been unable to successfully submit to the AIMO-3 competition due to persistent Kaggle system errors, and I’m hoping you might be able to help identify what’s going wrong.

For the couple of weeks, every submission attempt has resulted in a Kaggle error on the submissions page. I’ve tried a wide range of troubleshooting steps, including:

* Creating and submitting brand-new notebooks
* Re-submitting older notebooks that previously passed submission (though scored 0)
* Editing and re-saving notebooks before submission
* Submitting at different times of day and night
* Submitting from different devices and browsers

In all cases, the result is the same: the submission page reports Kaggle errors rather than a score or clear failure reason.

I’ve emailed [support@kaggle.com](mailto:support@kaggle.com) multiple times without receiving a response, and I posted on the AIMO-3 discussion board. The only suggestion I received there was to create a new notebook and submit it, which I did, but the errors persisted.

At this point, I don’t believe this is a widespread Kaggle outage, since other competitors are clearly able to submit, score, and iterate. That suggests the issue is likely something specific to my account, notebook state, or submission metadata. However, without any actionable error information beyond the generic “A system error. Please try resubmitting…”, I don’t have a way to diagnose or correct it.

I’ve invested a substantial amount of time into this competition, and being unable to submit at all is effectively blocking participation. While others can submit, see scores, and improve, I’m unable to even reach that first feedback step.

If you’re able to point me toward what might cause persistent submission-level errors like this, or advise on what to check (account state, notebook configuration, dataset bindings, versioning issues, etc.), I would really appreciate it.

For reference:

* Competition page: [https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/submissions](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/submissions)
* My profile: [https://www.kaggle.com/nadinesquires](https://www.kaggle.com/nadinesquires)

Thank you for your time, and for any guidance you can provide.

Best regards,
Nadine


### Reply 3 — N/A (2026-01-24)

This is a cherrypicked section of my submission history, I don't think it is a "very few teams" that submitted correct answers to either problem. (The version description is likely the old score)

![](https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F1680925%2F6b1a48a4086f358307b8eae0d4752712%2FScreenshot%202026-01-23%20at%2017.20.09.png?generation=1769217623309243&alt=media)


### Reply 4 — N/A (2026-02-01)

my all notebooks are failed and i shall not submit any notebook

### Reply 5 — N/A (2026-01-30)



### Reply 6 — N/A (2026-01-23)



### Reply 7 — N/A (2026-01-25)

Thanks for the update. @ryanholbrook 

---

## The Math Corpus Prize Repo
**ID:** 663330 | **Author:** Simon Frieder | **Date:** 2025-12-17 | **Comments:** 33

**Linked URLs:** https://www.kaggle.com/datasets/laureanoarcanio/the-multi-axis-profiled-mathematics-collection, https://github.com/laureano-arcanio/aimo3-dataset-pipeline/tree/main/authored_imo_style_problems, https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672685, https://github.com/laureano-arcanio/aimo3-dataset-pipeline, https://www.kaggle.com/code/laureanoarcanio/filtering-and-split-notebook/

### Reply 1 — N/A (2026-02-09)

## The Multi-Axis Profiled Mathematics Collection

### Links

[Dataset](https://www.kaggle.com/datasets/laureanoarcanio/the-multi-axis-profiled-mathematics-collection) 72k carefully selected with high accuracy metadata

[Crafted problems (PDF/LaTeX)](https://github.com/laureano-arcanio/aimo3-dataset-pipeline/tree/main/authored_imo_style_problems)

[Discussion](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672685)

[Full pipeline code](https://github.com/laureano-arcanio/aimo3-dataset-pipeline) Full end to end open source pipeline

[Filter and Split Notebook](https://www.kaggle.com/code/laureanoarcanio/filtering-and-split-notebook/) How to use this dataset to select levels, domanins and more.

[Analysis Notebook](https://www.kaggle.com/code/laureanoarcanio/multi-axis-dataset-exploratory-analysis) Full of charts that explains most of the decisions.

[Qwen 0.5B math model adapter checkpoint:](https://www.kaggle.com/models/laureanoarcanio/qwen2-5-coder-0-5b-instruct-algebra-specialist) Demostrating data targeting finetuning improves a strong coder model.



Thanks!

### Reply 2 — N/A (2026-02-09)

My submission for the Math Corpus prize:

- Dicussion: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672668
- Dataset: https://www.kaggle.com/datasets/nguyennguyen599/astral-math-v1

### Reply 3 — N/A (2026-02-09)

My submission for the Math Corpus Prize — CrystalMath: 2,129 verified, high-difficulty contest math problems for RLVR training.

Discussion write-up:
https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672592

Dataset:
https://huggingface.co/datasets/ycchen/Crystal-Math-Preview

Detailed report:
https://huggingface.co/datasets/ycchen/Crystal-Math-Preview/blob/main/CrystalMath_CAV_preprint.pdf

### Reply 4 — N/A (2026-02-08)

Here is my submission!

Discussion:

https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672528

Dataset:

https://www.kaggle.com/datasets/huikang/aimo3-corpus-prize-submission

### Reply 5 — N/A (2026-02-08)

Submission for Math Corpus Prize:                                                                                                         
                                                                                                                                            
  https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672507                                           
                                                                                                                                            
  - Dataset: https://www.kaggle.com/datasets/jordane95/aimo3-validation-benchmark                                                           
  - 347 validation problems with expert-verified integer answers (from BeyondAIME, AMO-Bench, IMO-AnswerBench)                              
  - 124 auxiliary RL training problems converted from non-integer formats

### Reply 6 — N/A (2026-02-10)

I am entering the Math Corpus competition:
 + Dataset: https://www.kaggle.com/code/sonphamorg/traces-h100-gptoss-curated
 + Write up: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672706

### Reply 7 — N/A (2026-02-10)

We’re all here to learn and improve!


### Reply 8 — N/A (2026-02-09)


Hi there!

I am entering my dataset for the Math Corpus Prize.

- Dataset: https://www.kaggle.com/datasets/sethmoudry/prism-math-aimo3/data

- EDA Starter Notebook: https://www.kaggle.com/code/sethmoudry/prism-math-eda

- Github: https://github.com/sethmoudry/prism-math

### Reply 9 — N/A (2026-02-09)

Hi! Please find our submission for the Math Corpus prize:

- Dataset: [https://www.kaggle.com/datasets/taraashmittal/aimo-3](https://www.kaggle.com/datasets/taraashmittal/aimo-3)
- The write-up: [https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672656](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672656)
- A tiny notebook for visualization: [https://www.kaggle.com/code/taraashmittal/using-our-aimo3-dataset](https://www.kaggle.com/code/taraashmittal/using-our-aimo3-dataset)

### Reply 10 — N/A (2026-02-09)

Submission for the Math Corpus Prize 
* Discussion: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672537
* Dataset: https://www.kaggle.com/datasets/mihailgribov/olympiad-style-integer-math-problems/data

### Reply 11 — N/A (2026-02-09)

Discussion write-up: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672699

Dataset: https://www.kaggle.com/datasets/chewkokwahibrainai/high-school-maths-exam/data

### Reply 12 — N/A (2026-02-09)

Our submission for the Math Corpus Prize: PolyMath

Discussion write-up: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672686

Dataset: https://huggingface.co/datasets/AIMO-Corpus/PolyMath

### Reply 13 — N/A (2026-02-09)

## Math Corpus - GPT-OSS-120B Tool-Integrated Reasoning Preference Pairs for OpenMathReasoning Additional Set


**Discussion Write-Up**: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672659

**Dataset**: https://huggingface.co/datasets/VITHURSHAN/DFO-Kaggle


### Reply 14 — N/A (2026-02-09)

Submission for AIMO - Progress Prize 3 Math Corpus

Discussion write-up: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672639

Dataset: https://www.kaggle.com/datasets/vijayashantim/aiom3-math-corpus

### Reply 15 — N/A (2026-02-09)

Submission for the Math Corpus Prize 

* Discussion: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672643
* Dataset 1: https://www.kaggle.com/datasets/zfturbo/hard-math-problems-for-aimo-3
* Dataset 2: https://www.kaggle.com/datasets/zfturbo/math-datasets-aimo-format

### Reply 16 — N/A (2026-02-09)

My submission for Math Corpus Prize 

Discussion Write up:

https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672575

Dataset: 

https://www.kaggle.com/datasets/aneeshmukkamala/aimo3afq

### Reply 17 — N/A (2026-02-07)

Hey @friederrr to be sure the deadline is 11:59 PM UTC on the February 9th correct? Trying to submit by tomorrow the 8th but there's much to do!

### Reply 18 — N/A (2026-02-07)

Hi, I participated in the Math Corpus Prize 3. Here is my information link.

Dataset 

https://www.kaggle.com/datasets/adyarezapahlevi/math-corpus-adya-dataset-9-0/data

discussion :

https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672398

### Reply 19 — N/A (2026-02-08)

Hi Simon, I am officially submitting the "AIMO 3: Refined Integer-Only Math Reasoning Corpus" dataset for the Math Corpus Prize.

Dataset Link: 

https://www.kaggle.com/datasets/chethan805/aimo-3-refined-integer-only-math-reasoning-corpus

Discussion Post:

https://www.kaggle.com/datasets/chethan805/aimo-3-refined-integer-only-math-reasoning-corpus/discussion/672470

### Reply 20 — N/A (2026-02-06)

I am entering my dataset for the Math Corpus Prize.

Dataset Name: Hard Math SFT

Dataset Link: [Link](https://www.kaggle.com/datasets/sangrampatil5150/hard-maths)

Detailed Write-up: Coming Soon

### Reply 21 — N/A (2026-02-07)


Hi team,

Submitting my entry for the **Math Corpus Prize**.

* **Dataset:** [AIMO3 Benchmark](https://www.kaggle.com/datasets/ritwikakancharla/aimo-3-benchmark/)
* **Discussion Thread:** [AIMO3 Benchmark: 400 Expert Problems (Eval & CoT)](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/672246)

This dataset adapts Google DeepMind's IMO-Bench into 400 expert-level problems, processed into **strict integer evaluation** (Leaderboard Simulator) and **advanced reasoning** (CoT) splits to aid in model training and validation.

Thanks!

### Reply 22 — N/A (2026-02-05)

Hello @friederrr 

I kindly request your clarification on something.

this is super late and this could just be me being paranoid but I just wanted to be sure

```Note that due to popular request, we have increased the character size from 50k to 100k, but we won't increase this further. ``` 

this is the answer length right ? whatever is spit out by the llm ? not the prompt + question + answer ?
and also simple pythonic len(text) and not the tokenized characters count ? 


I am asking this because it was mentioned as this ```Each datapoint is not allowed to exceed more than 100k characters```
So datapoint here means row wise summation or row-column entry wise?

Because, for a single question if my dataset has answers from multiple passes which could be RL type preference based data, how would that be counted? 

### Reply 23 — N/A (2026-02-05)

I have a question can we updatee the dataset until given time?
or once submitted we can't update the dataset!

### Reply 24 — N/A (2026-02-05)

Here is my dataset attachment, this is the link https://www.kaggle.com/datasets/uttarashah/amio3-dataset
https://www.kaggle.com/datasets/uttarashah/enhanced-aomo3-dataset

### Reply 25 — N/A (2026-02-01)

I am happy to enter the Math Corpus Prize Competition with the following:

1. Discussion: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671427

2. Dataset: https://www.kaggle.com/datasets/jeannkouagou/aimo3-tool-integrated-reasoning

### Reply 26 — N/A (2026-02-04)

I am entering my dataset for the Math Corpus Prize.

Dataset Name: Math Corpus GRPO Dataset

Dataset Link: [Link](https://www.kaggle.com/datasets/sangrampatil5150/math-corpus-grpo-2-6k-dataset/data/data/data)  Final V5

Detailed Write-up: [Link](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671107)

### Reply 27 — N/A (2026-02-04)

@friederrr Hello! I’m very excited to participate in the Math Corpus Prize. Below is my submission—please kindly review it. Thank you very much!

Link to Discussion:

[https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671815](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671815)

Dataset :

[https://www.kaggle.com/datasets/wenliangtlh/aimo3-high-difficulty-tool-calling-dataset/data](https://www.kaggle.com/datasets/wenliangtlh/aimo3-high-difficulty-tool-calling-dataset/data)


### Reply 28 — N/A (2026-02-03)

Hi this is my submission for the math corpus:--- [discussion thread](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/671520)

Dataset link:--- [check here](https://www.kaggle.com/datasets/ngarai/aimo3-rag-dataset-model-training)

-----Team 'Corvus'

### Reply 29 — N/A (2025-12-17)

```python
Performance (50 points)
Does the dataset improve mathematical reasoning and aid in improving model performance during the AIMO3. How so and how much?

```

Am I right in assuming "how much your dataset improves LLM's reasoning abilities" will be measured by the difficulty of the questions it helps solve?   Ie, similar metric as used by the Hard Problem Prize?  Who's responsibility will it be to show this via ablation?  This might be tricky as it's not clear what are the hard problems.

The reason I ask is I can imagine a significant number of different scenarios where a dataset could improve results that are trivially improved by other mechanisms (better tool calling, prompting changes / improvements, model selection, etc) and I think would have debatable value.   
  
I suppose one way of doing it is simply whoever has a dataset which increases the top end the most, but if that's the case, can we assume that 40 -> 41 is more valuable than 38-> 40? (just purely for example!  I am making the assumption here that 39 and 40 are 'easy' and '41' is hard.   You folks would know better what are the hard question ranges).  

The former would require a model that can achieve 40 and go to 41.   I can imagine scenarios where someone has a  model that can't solve some easy questions because they are using their dataset to focus their efforts on the hard stuff.   This would still have significant value, ofc.

There are other ways to show this, such as local cross validation with hard datasets.  If it's still also judged by the public LB, there will be some info leakage.  Is it right to assume the Corpus prize will be awarded after competition end?  Will people have until competition end to show ablation studies?  Private LB could be used as well for judging in that case, though showing by ablation would be risky :D

It's possible you're expecting other participants will use the dataset and you'll have enough datapoints to help judge better without definitive ablation studies.  That would certainly make things clearer and better for everyone.  Hopefully we get cool datasets like that!

### Reply 30 — N/A (2026-02-10)



### Reply 31 — N/A (2026-02-09)



### Reply 32 — N/A (2026-02-05)



### Reply 33 — N/A (2026-02-03)



---

## Clarifying the Longest Leader Prize 
**ID:** 663423 | **Author:** Simon Frieder | **Date:** 2025-12-17 | **Comments:** 3

**Linked URLs:** https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F3967558%2F7c9ff38c63dc5d4f86c6d613378ad48f%2Fimage_2026-01-24_090120309.png?generation=1769216483691457&alt=media

### Reply 1 — N/A (2026-01-01)

Assuming no mergers, all times in UTC:

- ~~For Siancy to win, Siancy needs to stay at the top until at least January 24, 2026, at 05:14:51 (2035418s from 2025-12-31 15:51:13).~~

- ~~For everyone else who has not been at the top, you need to climb to the top of the leaderboard before January 10, 2026, at 10:35:22 AM (2035418s before February 2, 2026 11:59 PM) and stay there.~~



### Reply 2 — N/A (2026-01-24)

Helping to confirm an assumption which I think will affect top teams decision:
1. Is the deadline for Team Merger (which will combine their score) same as the deadline for Public Notebook release, i.e February 9, 2026 11:59 PM UTC, which mean that all potential winners will be allow to negotiate till 9 Feb before they find the best partner to merge and combine their score?

This is logical assumption because a Team might not be able to fully confirm their final position and score before the end of scoring deadline (i.e. 2 Feb), and thus difficult to make an inform decision prior to that.

But I think it will be better if Host @friederrr can officially confirm it to avoid confusion.

### Reply 3 — N/A (2026-01-24)

If any 2 of the Top 3 merge, they will guarantee a win.
The ideal merger will be between the earlier Leaders, i.e. Just a test ( @yiyangzheng ) + Yi-Chia Chen ( @threerabbits) , then we will be able to understand more about their journey in achieving such a big lead so early ahead in time.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F3967558%2F7c9ff38c63dc5d4f86c6d613378ad48f%2Fimage_2026-01-24_090120309.png?generation=1769216483691457&alt=media)

i.won.a.maths.debate and Siancy also deserving a big appreciation regardless of whether they win at the end because of their selfless sharing of Top scoring notebook.

---

## Team Size Limit Increase to 20
**ID:** 663402 | **Author:** Addison Howard | **Date:** 2025-12-17 | **Comments:** 4

**Linked URLs:** https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/639476#3348005

### Reply 1 — N/A (2025-12-23)

I hope you’re doing well. I’m reaching out to ask whether you are currently open to adding new members to your team for the AI Mathematical Olympiad – Progress Prize 3 competition

### Reply 2 — N/A (2025-12-17)

Very very exciting!  Hopefully this comp makes some waves.   Note the post about submission limits impacting your ability to merge - https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/639476#3348005

>Team mergers will combine the longest leader duration of teams, but note: 1) Teams cannot unmerge after merging, and 2) You will not be able to merge teams whose combined daily submission count exceeds the total submission limit to that date (daily limit x number of days). With a daily submission limit of 1, this will limit merging opportunities.

### Reply 3 — N/A (2025-12-18)

So glad you did this I requested it for last year as we were more than 7 nvidians interested to work on it. But it was denied at the time. We didn't play the gray area, but as a result some of us, me included, were frustrated to not being able to enter.

### Reply 4 — N/A (2026-01-29)

Great news!

---

## Welcome to AIMO3: IMO-level problems, H100s, ecosystem, extra prizes
**ID:** 635859 | **Author:** Simon Frieder | **Date:** 2025-11-20 | **Comments:** 25

**Linked URLs:** https://www.imo-official.org/problems.aspx, https://matharena.ai/

### Reply 1 — N/A (2026-02-03)

@friederrr On the **Robustness** part, it is certainly better to run the evaluation on the private leaderboard twice rather than only once. However, we have seen in some notebooks how luck is a major factor and what if somebody gets so lucky twice? - which is highly probable given how many contestants there are. At the same time I understand that every evaluation run consumes a lot of resources.

What about something like you run the evaluation on the private leaderboard twice for everyone. And then for the top 5% you run it 3 more times. For the top 5% of the contestants, each run would have a weight of only 0.2 since we have 5 runs in total as opposed to having a weight of 0.5 in case of two runs. You can think of appropriate percentiles and the number of runs, perhaps, out of top 5%, the final top 50 can have even 10 runs in total, etc.? Hopefully, this would be a more fair way to reward those whose solution is consistent and not just lucky, but it would not put too much strain on the resources.

### Reply 2 — N/A (2026-01-21)

Simon, can you please give me an answer to this problem Im having... KAGGLE ERROR
ITS BEEN DAYS SUCK WITH GETTING KAGGLE ERRORS. IVE CONTACTED SUPPORT@KAGGLE.COM WITH NO SUCCESS.  My whole submission page is just a list of kaggle error submissions. On the website it says that this is rare and to try resubmitting. Ive lost weeks of being able to submit and participate. Could you please give me some kind of help. Ive invested so much time into this competition to be eliminated before even starting. I have had 2 successful submissions, so i know it has the potential to work. PLEASE HELP!! 

### Reply 3 — N/A (2026-01-13)

Anyone know if the 2 private set runs will be completely independent runs (ie different orders) or will they have the same order? 

### Reply 4 — N/A (2025-12-25)

> We are the first large-scale competition to have secured 128 H100 GPUs and Tinker credits for you to finetune your models, free of charge.

Are there updates from Tinker? I am looking forward to finetuning on their platform

### Reply 5 — N/A (2025-12-09)

@friederrr I have a question about the Math Corpus Prize Requirements. 

`Each datapoint is not allowed to exceed more than 50k characters.` 

I think this is not appropriate, with the speed of H100, we can currently make 4-5 requests with 32k tokens in 5 hours with gpt-oss-120b. 32k output tokens are basically over 50k characters, not to mention input characters and metadata if any. Could you consider this? Based on the size of the competition, I think 100,000 characters per data point will yield high quality datasets.

### Reply 6 — N/A (2025-11-23)

Tech Q: Is there a plan or possibility for the image/driver to be updated to support cuda beyond 12.6 within this competition period?

### Reply 7 — N/A (2025-11-21)

Do we all get the questions in the same order, or is it shuffled?

### Reply 8 — N/A (2025-11-21)

Everyone can access H100 through public notebooks? Does 5 hour limit resets every week?

### Reply 9 — N/A (2025-11-21)

@friederrr I greatly appreciate your team initiative in bridging the gap between competitors accessing from large labs  and aspiring individuals without access to compute resources. 

### Reply 10 — N/A (2025-12-07)

Hi everyone,

I’m still in the process of gathering information about the competition so I can understand whether I’m ready to participate. The discussions here have been really helpful so far, especially the clarifications about the evaluation process, H100 usage, and how the reference set should be interpreted.

### Reply 11 — N/A (2025-12-02)

If possible, please inform me quickly.

### Reply 12 — N/A (2025-12-02)

Can you tell me what needs to be done in this competition's notebook?


### Reply 13 — N/A (2026-01-24)

"Aligned with the new AIMO3 guidelines regarding stability, our pipeline was specifically engineered to ensure consistent outputs across multiple runs, acknowledging the new scoring penalty for unstable models. By decoupling reasoning from execution via SymPy, we address the 5-digit precision requirement without relying on stochastic arithmetic.

### Reply 14 — N/A (2025-12-28)

Hi @friederrr can you please help me with a confusion I have - I tried submitting a notebook earlier today but it failed with an error. With some modifications I wanted to make another submission attempt but it is blocked for the day with a message that says
>Cannot submit
Your team has used its daily Submission allowance (1) today, please try again tomorrow UTC (7.5 hours from now).

Does a failed submission attempt also count as a submission for the day?

### Reply 15 — N/A (2025-12-15)

Hi Everyone

This is a bit of a dumb question, so please forgive me.

We need to create our own datasets and then train our models. I am presuming one extremely time consuming way is to go this website

https://www.imo-official.org/problems.aspx (IMO past papers)

Then get the questions into Latex with answers and train them.

Is this allowable under competition rules?

### Reply 16 — N/A (2025-12-10)

For this comeptition, can we form a group of about 20 people and work together, and have only 8 representatives form a team on Kaggle?
Of course, this assumes the other 12 people will not submit any notebooks on kaggle or do not have Kaggle accounts.
@friederrr

### Reply 17 — N/A (2025-12-04)

Hey, i want to ask if there is any correlation between the reference set and the public set. Means the level of difficulty etc.

Because i have seen a very irregular patterns, 
The notebook that is giving 7/10 on reference set is giving 24/50 on public LB.
And the notebook that is giving 8/10 on refernce set is giving 6/50 on public LB.

So is the submission the only way to test the pipeline?

### Reply 18 — N/A (2025-11-23)

It is allowed for us to use H100 to fine-tuning model on kaggle?

### Reply 19 — N/A (2025-11-22)

@friederrr, As per Qwen docs,"""All our open-source models, except for the 3B and 72B variants, are licensed under Apache 2.0. You can find the license files in the respective Hugging Face repositories. It is NOT necessary for you to submit a request for commercial usage.""" So it means 3B and 72B  can't be listed under the whitelist models category. As you mentioned in the previous competition, the clause regarding user thresholds is mainly the reason for not being whitelisted.

### Reply 20 — N/A (2025-11-21)

❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️

### Reply 21 — N/A (2025-11-21)

Hiiiiiiiiiiii

### Reply 22 — N/A (2025-11-21)

Could you get the (novel) problems up on https://matharena.ai/ as well?

I think it is a good place for people to see how the LLM responds to the 10 reference problems.

### Reply 23 — N/A (2025-11-21)



### Reply 24 — N/A (2025-12-05)

Thanks for the information!

### Reply 25 — N/A (2025-11-23)

Thanks for the information!

---

## Longest Leader Prize Clarification
**ID:** 639476 | **Author:** Addison Howard | **Date:** 2025-11-24 | **Comments:** 4

### Reply 1 — N/A (2025-12-15)

Who are currently the frontrunners for the longest leader prize?

### Reply 2 — N/A (2025-12-29)

Given the variance in the comp, do all submitted notebooks have to be revealed that got the highest score or just one of the leader's choosing?  Or just the first?  Or the last? This is a different question than the merger case.

Does all data / fine tuning efforts need to be revealed?

This can, in theory, be rewarded early as well - even with team mergers.  The benefit being people can start leveraging sooner.  I think around halfway between now and the end date, minus a few days, assuming the current LB leader holds on.






### Reply 3 — N/A (2025-11-24)

How do you consider team mergers? Let's say we have three teams with 30 days, 30 days and 40 days at the top of the leaderboard and the total duration is 100 days.

If the two teams with 30 days at the top of the leaderboard merges, do they beat the team with 40 days at the top of the leaderboard?

One way to avoid facing this scenario is only the consider the maximum tenure among all team mergers.

### Reply 4 — N/A (2025-11-24)

Cool, the alternative (notebook has to be public at submission) does not really make sense because the moat is just the 5 hour run time and other contestants could submit and publish something that just happens to be better.

Also I notice it is "second longest tenure in first place", which is different from "as if the competition has happened without the highest ranking team". This means that being at second place at any point in time does not help you. This is good, because it is much easier to calculate who is in the line of succession.

---

## How to Get Started + Competition's Official Discord
**ID:** 634385 | **Author:** Addison Howard | **Date:** 2025-11-19 | **Comments:** 2

### Reply 1 — N/A (2025-12-07)

Hello Addison, 

May i know where is the file that hold the 50 mathematical questions we are asked to tackle on ? 

Thank you,
Kyle 

### Reply 2 — N/A (2025-11-24)

Where is exact question.I am new to kaggle please help me.

---

## Anyone tried qwen 3.5 models?
**ID:** 679339 | **Author:** NNMax | **Date:** 2026-02-28 | **Comments:** 4

**Linked URLs:** https://www.kaggle.com/code/shelterw/qwen3-5-w-python, https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F9785820%2F541d0bb25b5d36269ac2e27ec7bad802%2FEkran%20Resmi%202026-02-28%2022.45.18.png?generation=1772308144898966&alt=media

### Reply 1 — N/A (2026-03-01)

https://www.kaggle.com/code/shelterw/qwen3-5-w-python

Have you tried it yet?

### Reply 2 — N/A (2026-02-28)

Qwen 3.5 27B is a dense model, which means all 27B parameters are active during inference, so it really has no chance of matching the speed of oss-120B, since that one is a Mixture-of-Experts model with only about 5.1B active parameters at inference time.

The 35B-A3B variant should have a better chance in terms of speed since it is also a MoE, but from what I’ve observed is Qwen models tend to be more verbose in their reasoning, and artificial analysis benchmark seems to reflect that behavior.

In my small tests, 35B-A3B actually beats oss-120B without tools, but so far I haven’t been able to implement it reliably with tools using vllm.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F9785820%2F541d0bb25b5d36269ac2e27ec7bad802%2FEkran%20Resmi%202026-02-28%2022.45.18.png?generation=1772308144898966&alt=media)


### Reply 3 — N/A (2026-02-28)

The issue with the Qwen3.5 models is not hardware but the architecture per se; `Gated DeltaNet` is totally new and vLLM is not yet optimized for the Qwen3.5 series. It will likely take a couple of weeks (if not months) for Qwen3.5 to have the optimization level of GPT-OSS models, and that will be for Blackwell GPUs (not the H100s used in this competition). 

Ergo, I'd argue that the Qwen3.5 series would be useful for the AIMO4 competition.

### Reply 4 — N/A (2026-03-01)

I don't have anything to say except I hope more people chime in because experienced opinions help shape decisions less experienced like myself make and will likely save us quite a few hours too.

---

## Leaked DeepSeek-V4-Lite?
**ID:** 678966 | **Author:** ShelterW | **Date:** 2026-02-26 | **Comments:** 6

**Linked URLs:** https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F9052057%2Ff716ca324f3b07d4d1824369140e2bad%2Flb2.png?generation=1772167839620867&alt=media, https://www.kaggle.com/competitions/map-charting-student-math-misunderstandings/leaderboard, https://huggingface.co/collections/Qwen/qwen35

### Reply 1 — N/A (2026-03-01)

The name of the 1st place team is now "just public 44, all is luck". This is what I expected. But it also shows that this same public notebook could end up winning the first place. Low probability, but it could happen, it all depends on the mood of gpt-oss-120b:)

### Reply 2 — N/A (2026-02-26)

It has to be GPT-OSS, and probably a public notebook, LOL. A new model would require prior trial and failures

### Reply 3 — N/A (2026-02-27)

![](https://www.googleapis.com/download/storage/v1/b/kaggle-forum-message-attachments/o/inbox%2F9052057%2Ff716ca324f3b07d4d1824369140e2bad%2Flb2.png?generation=1772167839620867&alt=media)

This sort of thing happens.   https://www.kaggle.com/competitions/map-charting-student-math-misunderstandings/leaderboard

Please be careful about throwing around accusations without proof. 

What I find interesting is that he's submitting now and not later on.  My guess is he's trying to capture the 'first submission' tie breaker rule.

### Reply 4 — N/A (2026-02-26)

The timing is curious with the Qwen3.5 models release 2 days ago. 

https://huggingface.co/collections/Qwen/qwen35 

Specifically the 27b or the 122b which seem like they could be intentionally challenging gpt-oss-120b

### Reply 5 — N/A (2026-02-26)

Why do you think that happened? He only has a single submission and his profile is basically empty. Don’t you think there could be some other kind of luck involved?

### Reply 6 — N/A (2026-02-26)

Something feels off. Surprisingly the contestant joined a couple days ago. Entered AIMO and submitted right away? Topped LB? Either it has to be someone with a alias account or luck. 

---

## Issue: Kept getting 0 score during Submission
**ID:** 679529 | **Author:** varianceofx | **Date:** 2026-03-02 | **Comments:** 1

### Reply 1 — N/A (2026-03-02)



---

## Question about evaluation API and GPU runtime
**ID:** 679451 | **Author:** rıza temizel | **Date:** 2026-03-01 | **Comments:** 1

### Reply 1 — N/A (2026-03-01)

On the first part, I believe the submission fails if the notebook exceeds the timelimit, though I've never had it happen so I can't say for sure.
On the seconds part, you see runtimes over 5 hours because they obfuscate the exact runtimes by up to half an hour.

---

## Issue with notebook submission
**ID:** 679188 | **Author:** Preet | **Date:** 2026-02-27 | **Comments:** 1

### Reply 1 — N/A (2026-02-28)

Hii buddy, this usually happens because the submission environment is different from your local run.

A few things you have to check:

🔹 Make sure predict() is actually being called during submission (add simple print() logs to confirm).
🔹 Check that the KAGGLE_IS_COMPETITION_RERUN condition is working correctly and serve() is running.
🔹 Be careful with asynchronous server start (Popen) — the server might not be fully ready when inference starts.
🔹 Load your model inside predict(), not before serve().

Adding debug logs is the best way to find where it stops. Hope this helps! 🚀

---

## OS Page Cache Loading 7x Slower Than Usual — Causing Submission Errors?
**ID:** 678800 | **Author:** Van-Phuc Huynh | **Date:** 2026-02-25 | **Comments:** 4

### Reply 1 — N/A (2026-02-25)

I also encountered a very slow model loading issue around 0:00 UCT (~ 4 hours ago), which led to the submission timeout with "Notebook Inference Server Never Started" error.

For the past few hours, the model loading on kaggle notebook (w/ H100) has been super slow, but now it seems to be working as usual. Not sure if it is just a transient issue or due to some resource contention.

### Reply 2 — N/A (2026-02-25)

Unfortunately, I encountered a “Notebook Inference Server Never Started” error and lost one submission today because of it. What happened?

### Reply 3 — N/A (2026-02-25)

It seems to have been resolved now right? My submission is running 

### Reply 4 — N/A (2026-02-25)

hey @ryanholbrook, @herbison can you please tell what is the problem , and resolve it if possible.

---

## Inference engines other than vllm
**ID:** 676019 | **Author:** Darren Amadeus Martin | **Date:** 2026-02-23 | **Comments:** 2

### Reply 1 — N/A (2026-02-23)

i think air LLM may be a good choice

### Reply 2 — N/A (2026-02-25)

I also tried using SGLang, but the inference was a bit slower. I modified the code based on the public notebook, using the `/generate` endpoint to get token_ids.

---

