from openai import OpenAI

class CBotGPT:
    """
    This class represents a gpt object to have multiple gpt sessions in parallel.
    """

    def __init__(self, sys_msg:str):
        """
        set openai.api_key to the OPENAI environment variable
        :param sys_msg: initialization system message. what is the bot used for?
        """
        self.client = OpenAI(api_key="set_your_api_key_here")
        self.msgs=[{"role": "system", "content": sys_msg}]


    def send_qry(self, qry:[str]):
        """
        send new query to gpt
        :param qry: new query
        :return: response from gpt
        """
        # make sure the query is a list
        qry = qry if type(qry) == list else [qry]
        # append all messages alternating user and assistant to message list
        for i in range(len(qry)):
            self.msgs.append({"role": ("user" if i%2==0 else "assistant"), "content": qry[i]})

        response = self.client.chat.completions.create(model="gpt-4o", messages=self.msgs)
        resp_msg = response.choices[0].message.content

        # reset message history
        self.msgs = [self.msgs[0]]

        return resp_msg



