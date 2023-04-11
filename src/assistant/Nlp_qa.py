from transformers import pipeline

bert_model = pipeline("question-answering", model='distilbert-base-cased-distilled-squad')
"""pipeline: The pre-trained BERT Question-Answer model"""


def bert_qa(question: str, context: str):
    """Method provides a simple interface to utilize the BERT model, by providing the question to answer and the
    contextual information.

    Args:
        question (str): The question Kurt wants to answer
        context (str): The contextual information from which the answer can be extracted.
    """
    answer = bert_model(question=question, context=context)
    return answer['answer'], answer['score']

