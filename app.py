"""
This script is a demo for a chatbot implementing character computing for answer generation.
After initialisation (training of gpt) the bot forwards the query to gpt for extracting
character defining components. Subsequently, it requests gpt to generate a reply for the prompt
by considering previously identified character parameters.

The script can be started with the optional parameter --plain. In this case, the flavoring is disabled.
"""

from flask import Flask, render_template, request, session
from CBotGPT import CBotGPT
from enum import Enum
import datetime
from ilio import read       # read file in one line
import random as rd
import os
import statistics as stat

# global variables
app = Flask(__name__)
app.secret_key = os.urandom(12)
min_chat_interactions = 4
n_c_vec_in_b = 3                 # number c history elements used for b_vector
empty_char_vect = {"neuroticism":[], "extraversion":[], "openness":[], "agreeableness":[], "conscientiousness":[]}

analytic_bot = None
backend_bot = None
flavor_bot = None

class dType(Enum):
    BOT = 'bot: '
    FLA = 'fla: '
    USR = 'usr: '
    CHR = 'chr: '
    ERR = 'err: '
    SUR = 'sur: '
    CLR = ''

def dump_chat(txt:str, t_msg:dType):
    """
    write the last entry of the story memory to the dump file.
    :param t_msg: type of dump message
    :param txt: text for adding to dump file
    :return: None
    """
    chat_dump_fn = session.get('chat_dump_fn')

    with open(chat_dump_fn, 'a') as f:
        f.write(t_msg.value + txt + "\n")

def read_file(fn):
    """
    read full file at once and returns the content as string
    :param fn: file name
    :return: file content
    """
    with open(fn, 'r') as f:
        return f.read()

def estimate_b_vect(c):
    """
    The function appends recent calculated c vector to the c-vector history and
    cuts off the history to n most recent elements. Based on updated history, it
    returns the average of each character in the c-vector history as b vector.
    :param c: character vector of most recent user input.
    :return: estimated b vector: mean character vector of n most recent c-vectors.
    """
    # typecast character dictionary from str to dict format
    c = eval(c)
    # init b vector
    b = empty_char_vect
    # load history from session variable
    c_hist = session.get('c_history')
    for k in c:
        c_hist[k] = (c_hist[k] + [c[k]])[-n_c_vec_in_b:]
        b[k] = stat.mean(c_hist[k])

    # save updated c history to session variable
    session['c_history'] = c_hist

    return b

@app.route('/')
def main():
    """
    main method called when website (i.e. main.html) is called.
    :return: update main.html
    """
    # init three different chatbots: one for analyzing query characters, one as backend (company bot) and a third for
    # flavoring the response message based on the query characters
    global analytic_bot, backend_bot, flavor_bot
    story = ["You are here to support the evaluation of the character computing chatbot concept. As test user, you interact with a chatbot, "
             "that replies either in character flavoured style or the regular plain language style. The full conversation will be recorded. You can "
             "only participate when you agree this condition with YES. Alternatively, close the interface and no recording will be taken."
             "\n\nThanks for your support.\nSophie Hundertmark and Ramón Christen"]

    analytic_bot_char = read_file("prompts/analytic_bot.txt")
    backend_bot_char = read_file("prompts/backend_bot.txt")
    flavor_bot_char = read_file("prompts/flavor_bot.txt")

    # parameter for turning off character computing
    p_plain = request.args.get('-plain', default=rd.random()<0.5, type=bool)
    pp_plain = request.args.get('-plain', default=False, type=bool)


    # parameter for enabling log at the end ond chat
    show_log = request.args.get('-show_log', default=False, type=bool)

    # init session
    # set filename for chat dump: suffix _plain for plain bot and _character for character flavoured bot
    session['chat_dump_fn'] = str(datetime.datetime.now()) + ("_plain" if p_plain else "_character")
    session['p_plain'] = p_plain
    session['show_log'] = show_log
    session['confirmed'] = False
    session['qry_cnt'] = 0
    session['board_story'] = []
    session['flavored_story'] = []
    session['backend_story'] = []
    session['c_history'] = empty_char_vect

    analytic_bot = CBotGPT(analytic_bot_char)
    backend_bot = CBotGPT(backend_bot_char)
    flavor_bot = CBotGPT(flavor_bot_char)

    return render_template('main.html', story="\n".join(story))

@app.route("/send_qry/", methods=['POST'])
def send_qry():
    """
    send query to chatbots for identifying characters and/or getting reply from plain bot.
    :return: send result to html
    """
    global analytic_bot, backend_bot, flavor_bot
    missing_confirm = 'Unfortunately you did not confirm the conditions. Please leaf the page or confirm with: yes'

    # read session variables
    confirmed = session.get('confirmed')
    p_plain = session.get('p_plain')
    board_story = session.get('board_story')
    qry_cnt = session.get('qry_cnt')
    flavored_story = session.get('flavored_story')
    backend_story = session.get('backend_story')
    c_hist = session.get('c_history')
    qry = request.form.get('qry_txt')

    try:
        if confirmed:
            qry_cnt += 1

            # update story lists with query; underline category: \u0332
            board_story.append("\u0332".join("User: ") + qry)
            flavored_story.append(qry)
            backend_story.append(qry)

            # initialise local variables
            c = "-- no query character analysis --"
            r = backend_bot.send_qry(backend_story)
            b = "-- no chat character analysis --"

            # estimate characters of last query
            c = analytic_bot.send_qry('characterize the following input: "' + qry + '"')
            # character vector b is calculated including character of last query
            b = estimate_b_vect(c)

            # check app mode: plain or flavored
            if not p_plain:
                f = flavor_bot.send_qry("rephrase the text (T) by considering the full story (S), the behavior (B) and the character of the last "
                                        "query (C).\n"
                                        "- T is: '{0}'\n"
                                        "- S is: '{1}'\n"
                                        "- B was estimated as: {2} and \n"
                                        "- C was estimated as: {3}.".format(r, flavored_story, b, c))
            else:
                f = r

            # append story_lists with plain and flavored replies
            backend_story.append(r)
            flavored_story.append(f)
            board_story.append("\u0332".join("Bot: ") + f)

            # dump story information
            dump_chat(qry, dType.USR)
            dump_chat(r, dType.BOT)
            dump_chat(f, dType.FLA)
            dump_chat("B = " + str(b), dType.CHR)
            dump_chat("C = " + str(c), dType.CHR)

        elif qry.lower().strip() in ["yes","ja","oui","ok","start"]:
            confirmed = True
            welcome_msg = 'Hello, I am the chat bot of Dr. Test. How can I help you with?'
            board_story = [welcome_msg]
            # dump init bot welcome message
            dump_chat(welcome_msg, dType.BOT)
        else:
            board_story.append(missing_confirm)
    except Exception as e:
        dump_chat(str(e), dType.ERR)
    finally:
        # if not enable_survey:
        dump_chat('\n---------------------', dType.CLR)

        # set session variables
        session['confirmed'] = confirmed
        session['board_story'] = board_story
        session['flavored_story'] = flavored_story
        session['backend_history'] = backend_story
        session['qry_cnt'] = qry_cnt

    return render_template('main.html', story="\n".join(board_story), allow_survey=(qry_cnt>=min_chat_interactions))

@app.route("/send_survey/", methods=['POST'])
def send_survey():
    """
    log answers of the survey
    :return: None
    """
    p_plain = session.get('p_plain')
    show_log = session.get('show_log')
    pers = request.form.get('pers5')
    emp = request.form.get('emp3')
    emo = request.form.get('emo5')
    dump_chat("char: {0}, personality: {1}, emphatic: {2}, emotion: {3}, fb: {4}".format(not p_plain, pers, emp, emo, request.form.get('wellbeing')),
              dType.SUR)
    return render_template('main.html', enable_thankyou=not show_log, show_log=show_log, log_txt=read(session.get('chat_dump_fn')))

if __name__ == '__main__':
    app.run()

# plain=F -> character=T -> character= not plain
