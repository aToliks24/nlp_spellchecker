import re
import time
from enum import Enum

Deletion='deletion'
Insertion='insertion'
Substitution='substitution'
Transposition='transposition'

mistakesProbDict = {
    Insertion: dict(),
    Deletion: dict(),
    Substitution: dict(),
    Transposition: dict()
}
mistakesCountDict = {
    Insertion: dict(),
    Deletion: dict(),
    Substitution: dict(),
    Transposition: dict()
}

charactersCountDict = dict()

MAX_MISTAKES_IN_WORD=3


def delition(cp_m_1, cp):
    if (cp_m_1 , cp) not in mistakesCountDict[Deletion] or cp_m_1 + cp not in charactersCountDict:
        return 0
    return (mistakesCountDict[Deletion][(cp_m_1 , cp)]) / (charactersCountDict[cp_m_1 + cp])
def insertion(cp_m_1, tp):
    if (cp_m_1 , tp) not in mistakesCountDict[Deletion] or cp_m_1 not in charactersCountDict:
        return 0
    return mistakesCountDict[Insertion][(cp_m_1 , tp)] / charactersCountDict[cp_m_1]
def substitution(tp,cp):
    if (tp , cp) not in mistakesCountDict[Deletion] or cp not in charactersCountDict:
        return 0
    return mistakesCountDict[Substitution][(tp , cp)] / charactersCountDict[cp]
def transposition(cp,cp_p_1):
    if (cp , cp_p_1) not in mistakesCountDict[Deletion] or cp + cp_p_1 not in charactersCountDict:
        return 0
    return mistakesCountDict[Transposition][(cp,cp_p_1)] / charactersCountDict[cp+cp_p_1]

funcDict={Insertion:insertion,Deletion:delition,Substitution:substitution,Transposition:transposition}

def calculateProbability(type,a,b):
    return funcDict[type](a,b)

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
        insertToCountDict(v,ngramdict[k])
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
    mis='^'+tup[0]
    tru='^'+tup[1]
    lst=recGetMistake(mis,1,tru,1,0)#list[tup(errTypeList, errTupList)*]
    return lst


def recGetMistake(misake,mi,word,wi,i):
    mis=misake[mi:]
    tru=word[wi:]
    if i>MAX_MISTAKES_IN_WORD :
        return []
    elif len(mis)==len(tru)==0:
        return []
    elif mis=="":
        if i+len(tru)>MAX_MISTAKES_IN_WORD:
            return []
        else:
            res=[(Deletion,(word[wi-1],tru[0]))]
            for c in tru[1:]:
                res.append((Deletion,(c,'$')))
            return res
    elif tru=="":
        if i + len(mis) > MAX_MISTAKES_IN_WORD:
            return []
        else:
            res = [(Insertion,(misake[-1],mis[0]))]
            for c in mis[1:]:
                res.append((Insertion, ('$', c)))
            return res
    elif mis[0]==tru[0]:
            return recGetMistake(misake,mi+1,word,wi+1,i)
    else: #check errorType
        subslist=[(Substitution,(tru[0],mis[0]))]+recGetMistake(misake,mi+1,word,wi+1,i+1)
        inserlist=[(Insertion,(word[wi-1],mis[0]))]+recGetMistake(misake,mi+1,word,wi,i+1)
        dellist=[(Deletion,(word[wi-1],mis[0]))]+recGetMistake(misake,mi,word,wi+1,i+1)
        alllist = [subslist, inserlist, dellist]
        if len(tru)>1 and len(mis)>1 and tru[0]==mis[1] and tru[1]==mis[0]:
            translist=[(Transposition,(tru[0],mis[0]))]+recGetMistake(misake,mi+2,word,wi+2,i+1)
            alllist.append(translist)
        res=None
        for i in range(len(alllist)):
            if alllist[0][-1]!=None:
                if res==None:
                    res=alllist[0]
                elif len(res)>len(alllist[0]):
                    res=alllist[0]
            alllist = alllist[1:]
        if res==None:
            res=[]
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


    f=open(errors_file,'r')
    wholeFile=f.read().lower().split('\n')
    f.close()
    separated = errFileToTupleList(wholeFile)

    for tup in separated:
        errTups=getMistake(tup)
        for curr in errTups:
            errTup=curr[1]
            errType=curr[0]
            insertToCountDict(errTup,mistakesCountDict[errType])
    for word in lexicon.keys():
        for c in word:
            insertToCountDict(c, charactersCountDict)
        for i in range(len(word)-1):
            c=word[i]+word[i+1]
            insertToCountDict(c,charactersCountDict)
    global mistakesProbDict
    for etype in mistakesCountDict.keys():
        for tup in mistakesCountDict[etype]:
            p=calculateProbability(etype,tup[0],tup[1])
            mistakesProbDict[etype][tup]=p


def errFileToTupleList(wholeFile):
    separated = []
    for str in wholeFile:
        if '->' not in str:
            continue
        tup = str.split('->')
        if ',' in tup[1]:
            multiple = tup[1].split(',')
            for s in multiple:
                separated.append((tup[0].strip(), s.strip()))
        else:
            separated.append((tup[0].strip(), tup[1].strip()))
    return separated


def insertToCountDict(key, charactersCountDict):
    if key in charactersCountDict:
        charactersCountDict[key] += 1
    else:
        charactersCountDict[key] = 1


def getwords(lex):
    f=open(lex,'r')
    str=f.read().lower()
    filtered=re.findall('[a-z\x27\x2d]+',str)
    words=dict()
    for word in filtered:
        insertToCountDict(word,words)
    return words


t1 = time.time()
print(t1)
path=r'C:\Users\tolik\Desktop\wikipedia_common_misspellings.txt'
lex=r'C:\Users\tolik\Desktop\sharlock.txt'





lexicon=getwords(lex)
create_error_distribution(path,lexicon)
t2 = time.time()
print(str(t2)+'\n')
t2=t2-t1
print(t2)




def generate_text(lm, m=15, w=None):
    """ Returns a text of the specified length, generated according to the
     specified language model using the specified word (if given) as an anchor.

     Args:
        lm (dict): language model used to generate the text.
        m (int): length (num of words) of the text to generate (default 15).
        w (str): a word to start the text with (default None)

    Returns:
        A sequrnce of generated tokens, separated by white spaces (str)

    lm:=language model, m:=length of generated text
    evaluate_text(s,lm)   s=sentence, lm language model
    """



'''''
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
'''
def evaluate_text(s,lm):
    """ Returns the likelihood of the specified sentence to be generated by the
    the specified language model.

    Args:
        s (str): the sentence to evaluate.
        lm (dict): the language model to evaluate the sentence by.

    Returns:
        The likelihood of the sentence according to the language model (float).
    """
