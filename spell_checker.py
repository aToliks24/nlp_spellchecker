import re
import time
from enum import Enum
class MistakeType(Enum):
    Deletion=0
    Insertion=1
    Substitution=2
    Transposition=3

global MAX_MISTAKES_IN_WORD



def linsplitter(files):
    rgx1 = r'(?<=\w)[\x2e\x2d](?=\w)'  #U.S.A | key-word
    rgx2=r'[a-zA-Z]'
    ptrn=re.compile(rgx2)
    files=re.sub(rgx1,'',files)
    res1=files.splitlines()
    res=[]
    mapping = {'"':' ','?': ' ?', '!': ' !','-':' ',',':' '}
    for r in res1:
        for k, v in mapping.iteritems():
            r1 = r.replace(k, v)
            if ptrn.search(r1):
                res.append(r.lower())
    return res

def ngrams(words, n):
  res = []
  grm=words[0]
  for i in range(1,n):
    grm+=' '+words[i]
    res.append(grm)
  for i in range(len(words)-n+1):
    res.append(words[i:i + n])
  return res

def addToDict(ngramdict, grm):
    lst=grm.split(' ')
    k=lst[-1]
    v=lst[0:-1]
    if k in ngramdict:
        if v in ngramdict[k]:
            ngramdict[k][v]+=1
        else:
            ngramdict[k][v]=1
    else:
        ngramdict[k]=dict()
        ngramdict[k][v]=1
    return ngramdict

def learn_language_model(files, n=3, lm=None):
    """ Returns a nested dictionary of the language model based on the
    specified files.Text normalization is expected (please explain your choice
    of normalization HERE in the function docstring.
    Example of the returned dictionary for the text 'w1 w2 w3 w1 w4' with a
    tri-gram model:
    tri-grams:
    <> <> w1
    <> w1 w2
    w1 w2 w3
    w2 w3 w1
    w3 w1 w4
    w1 w4 <>
    w4 <> <>
    and returned language model is:
    {
    w1: {'':1, 'w2 w3':1},
    w2: {w1:1},
    w3: {'w1 w2':1},
    w4:{'w3 w1':1},
    '': {'w1 w4':1, 'w4':1}
    }

    Args:
     	  files (list): a list of files (full path) to process.
          n (int): length of ngram, default 3.
          lm (dict): update and return this dictionary if not None.
                     (default None).

    Returns:
        dict: a nested dict {str:{str:int}} of ngrams and their counts.
    """
    if lm==None:
        res=dict()
    else:
        res=lm
    sentences=linsplitter(files)
    for s in sentences:
        words=s.split(' ')
        ngrms=ngrams(words,n)
        for grm in ngrms:
            res=addToDict(res, grm)
    return res


def getMistake(tup):
    mis=tup[0]
    tru=tup[1]
    global MAX_MISTAKES_IN_WORD
    lst=recGetMistake(mis,tru,0)#list[tup(errTypeList, errTupList)*]
    return lst

def recGetMistake(mis,tru,i):
    if i>MAX_MISTAKES_IN_WORD :
        return [None]
    elif len(mis)==len(tru)==0:
        return []
    elif mis=="":
        if i+len(tru)>MAX_MISTAKES_IN_WORD:
            return [None]
        else:
            res=[]
            for c in tru:
                res.append((MistakeType.Deletion,(c,'-')))
            return res
    elif tru=="":
        if i + len(mis) > MAX_MISTAKES_IN_WORD:
            return [None]
        else:
            res = []
            for c in mis:
                res.append((MistakeType.Insertion, ('-', c)))
            return res
    elif mis[0]==tru[0]:
            return recGetMistake(mis[1:],tru[1:],i)
    else: #check errorType
        subslist=[(MistakeType.Substitution,(tru[0],mis[0]))]+recGetMistake(mis[1:],tru[1:],i+1)
        inserlist=[(MistakeType.Insertion,('-',mis[0]))]+recGetMistake(mis[1:],tru,i+1)
        dellist=[(MistakeType.Deletion,(tru[0],'-'))]+recGetMistake(mis,tru[1:],i+1)
        translist=[None]
        if len(tru)>1 and len(mis)>1 and tru[0]==mis[1] and tru[1]==mis[0]:
            translist=[(MistakeType.Transposition,(tru[0:2],mis[0:2]))]+recGetMistake(mis[2:],tru[2:],i+1)
        alllist=[subslist,inserlist,dellist,translist]
        res=None
        for i in range(len(alllist)):
            if alllist[0][-1]!=None:
                if res==None:
                    res=alllist[0]
                elif len(res)>len(alllist[0]):
                    res=alllist[0]
            alllist = alllist[1:]
        if res==None:
            res=[None]
        return res

def create_error_distribution(errors_file, lexicon):
    """ Returns a dictionary {str:dict} where str is in:
    <'deletion', 'insertion', 'transposition', 'substitution'> and the inner dict {tupple: float} represents the confution matrix of the specific errors
    where tupple is (err, corr) and the float is the probability of such an error. Examples of such tupples are ('t', 's'), ('-', 't') and ('ac','ca').
    Notes:
        1. The error distributions could be represented in more efficient ways.
           We ask you to keep it simpel and straight forward for clarity.
        2. Ultimately, one can use only 'deletion' and 'insertion' and have
            'sunstiturion' and 'transposition' derived. Again,  we use all
            four explicitly in order to keep things simple.
    Args:
        errors_file (str): full path to the errors file. File format mathces
                            Wikipedia errors list.
        lexicon (dict): A dictionary of words and their counts derived from
                        the same corpus used to learn the language model.

    Returns:
        A dictionary of error distributions by error type (dict).

    """
    mistakesDict={
    MistakeType.Insertion:dict(),
    MistakeType.Deletion:dict(),
    MistakeType.Substitution:dict(),
    MistakeType.Transposition:dict()
    }
    errCount=0
    f=open(errors_file,'r')
    wholeFile=f.read().lower().split('\n')
    f.close()
    separated=[]
    for str in wholeFile:
        if '->' not in str:
            continue
        tup = str.split('->')
        if ',' in tup[1]:
            multiple=tup[1].split(',')
            for s in multiple:
                separated.append((tup[0].strip(),s.strip()))
        else:
            separated.append((tup[0].strip(),tup[1].strip()))

    for tup in separated:
        errTups=getMistake(tup)
        for curr in errTups:
            errCount+=1
            errTup=curr[1]
            errType=curr[0]
            if errTup in mistakesDict[errType].keys():
                mistakesDict[errType][errTup]=mistakesDict[errType][errTup]+1
            else:
                mistakesDict[errType][errTup]=1
t1 = time.time()
print(t1)
path=r'C:\Users\tolik\Desktop\wikipedia_common_misspellings.txt'
create_error_distribution(path,None)
t2 = time.time()
print(t2+'\n'+t2-t1)



'''''
def generate_text(lm, m=15, w=None):
    """ Returns a text of the specified length, generated according to the
     specified language model using the specified word (if given) as an anchor.

     Args:
        lm (dict): language model used to generate the text.
        m (int): length (num of words) of the text to generate (default 15).
        w (str): a word to start the text with (default None)

    Returns:
        A sequrnce of generated tokens, separated by white spaces (str)
    """


lm:=language model, m:=length of generated text
evaluate_text(s,lm)   s=sentence, lm language model


def correct_word(w, word_counts, errors_dist):
    """ Returns the most probable correction for the specified word, given the specified prior error distribution.

    Args:
        w (str): a word to correct
        word_counts (dict): a dictionary of {str:count} containing the
                            counts  of uniqie words (from previously loaded
                             corpora).
        errors_dist (dict): a dictionary of {str:dict} representing the error
                            distribution of each error type (as returned by
                            create_error_distribution() ).

    Returns:
        The most probable correction (str).
    """


def correct_sentence(s, lm, err_dist,c=2, alpha=0.95):
""" Returns the most probable sentence given the specified sentence, language
model, error distributions, maximal number of suumed erroneous tokens and likelihood for non-error.

Args:
    s (str): the sentence to correct.
    lm (dict): the language model to correct the sentence accordingly.
    err_dist (dict): error distributions according to error types
                    (as returned by create_error_distribution() ).
    c (int): the maximal number of tokens to change in the specified sentence.
             (default: 2)
    alpha (float): the likelihood of a lexical entry to be the a correct word.
                    (default: 0.95)

Returns:
    The most probable sentence (str)

"""

def evaluate_text(s,lm):
    """ Returns the likelihood of the specified sentence to be generated by the
    the specified language model.

    Args:
        s (str): the sentence to evaluate.
        lm (dict): the language model to evaluate the sentence by.

    Returns:
        The likelihood of the sentence according to the language model (float).
    """
'''