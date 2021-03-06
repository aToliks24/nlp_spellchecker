from io import open
import re
import time
from pickle import dump,load
from random import choice
from itertools import product



Deletion='deletion'
Insertion='insertion'
Substitution='substitution'
Transposition='transposition'


#region learn_language_model

def linsplitter(strs):
    """ Returns a list of strings contains only characters [a-z\x2e\x27\x20\n]

       Args:
           strs (str): string of utf8 characters.

       Returns:
           A list of sentences that was separated by '.' or '\n'

       """
    rgx1 = r'(?<=\w)[\x2e\x2d](?=\w)'  #U.S.A | key-word
    rgx2=r'[^a-zA-Z\x2e\x27\x20\n]'
    strs = re.sub(rgx1, "", strs)
    strs=re.sub(rgx2, "", strs)
    strs=re.sub("\n+", " ", strs)
    strs = re.sub(r"\x20+", "\x20", strs)
    strs = re.sub(r"\x2e+", "\n", strs)
    res1=strs.splitlines()
    res=[]
    for r in res1:
        res.append(r.lower().strip())
    return res


def ngrams(words, n):
    """ Returns a list of list of strings with length of n

       Args:
           words (list): list of strings.
           n (int): number of words in each sub-list

       Returns:
           A list of list of strings which contains n words in each sub-list.

       """
    res=[]
    for i in range(len(words)-n+1):
        grm = []
        for j in range(i,i+n):
          grm.append(words[j])
        res.append(grm)
    return res


def addToMlDict(ngramdict, grm):
    """ Add another gram to language model dictionary.

       Args:
           ngramdict (dict): a dictionary of lm you wish to append another gram.
           grm (list): list of n words to insert the ngramdict.

       Returns:
           The dictionary of ngramdict with increased count value to the specific gram

       """
    k=grm[-1]
    v=grm[0:-1]
    if k in ngramdict:
        insertToCountDict(' '.join(v).strip(), ngramdict[k])
    else:
        ngramdict[k]=dict()
        ngramdict[k][' '.join(v)]=1
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
    fstr=""
    for p in files:
        with open(p,'r',encoding='utf8') as f:
            file=f.read()
            fstr+=file.encode('utf8')

    res = learn_lm_from_string(fstr,  n , lm)
    return res


def learn_lm_from_string(fstr,n,lm):
    """ A sub mudule of  learn_language_model.

       Args:
           fstr (string): a string to insert to lm.
           n (ins): number of grams.
           lm (dict): language model dictionaryas described in learn_language_model.

       Returns:
           dict: a nested dict {str:{str:int}} of ngrams and their counts.

       """
    if lm == None:
        res = dict()
    else:
        res = lm
    sentences = linsplitter(fstr)
    for s in sentences:
        words = [""] * (n - 1) + s.split(' ')
        ngrms = ngrams(words, n)
        for grm in ngrms:
            res = addToMlDict(res, grm)
    for k0 in res.keys():  # smoothing
        for k1 in res[k0].keys():
            res[k0][k1] += 1
    return res


#endregion

# region create_error_distribution
MAX_MISTAKES_IN_WORD=2


def calculateProbability(type,a,b,mistakesCountDict,charactersCountDict):
    """ Returns the probability of an error based on noisy channel language model.
        it uses different functions below based on the error type.

       Args:
           type (str): type of error (delition/insertion/substitution/transposition).
           a,b (int): (arguments needed for noisy chanel probabilities , each type has different arguments.
           mistakesCountDict (dict): count of each mistake from the common mispelings.
           charactersCountDict(dict): number of each character in the lm.

       Returns:
           A probability of the error.

       """
    return funcDict[type](a,b,mistakesCountDict,charactersCountDict)

def delition(cp_m_1, cp,mistakesCountDict,charactersCountDict):
    if (cp_m_1 , cp) not in mistakesCountDict[Deletion] :
        mistakesCountDict[Deletion][cp_m_1]=cp
    if cp_m_1 + cp not in charactersCountDict:
        charactersCountDict[cp_m_1 + cp]=1
    return float(mistakesCountDict[Deletion][(cp_m_1 , cp)]) / charactersCountDict[cp_m_1 + cp]



def insertion(cp_m_1, tp,mistakesCountDict,charactersCountDict):
    if (cp_m_1 , tp) not in mistakesCountDict[Insertion]:
        mistakesCountDict[Insertion][cp_m_1]=tp
    if cp_m_1 not in charactersCountDict:
        charactersCountDict[cp_m_1]=1
    return float(mistakesCountDict[Insertion][(cp_m_1 , tp)] )/ charactersCountDict[cp_m_1]



def substitution(tp,cp,mistakesCountDict,charactersCountDict):
    if (tp , cp) not in mistakesCountDict[Substitution] :
        mistakesCountDict[Substitution][tp]=cp
    if cp not in charactersCountDict:
        charactersCountDict[cp]=1
    return float(mistakesCountDict[Substitution][(tp , cp)]) / charactersCountDict[cp]



def transposition(cp,cp_p_1,mistakesCountDict,charactersCountDict):
    if (cp , cp_p_1) not in mistakesCountDict[Transposition]:
        mistakesCountDict[Transposition][cp]=cp_p_1
    if cp + cp_p_1 not in charactersCountDict:
        charactersCountDict[cp+cp_p_1]=1
    return float(mistakesCountDict[Transposition][(cp,cp_p_1)] )/ charactersCountDict[cp+cp_p_1]

funcDict={Insertion:insertion,Deletion:delition,Substitution:substitution,Transposition:transposition}




def getMistake(tup):
    """Wrapper of recGetMistake recursive function.

       Args:
           tup (tupple): str,str of a word and a misspelling of it.

       Returns:
           list of tupples , each tupple has a key of an edit-type-error string and value of the tow characters involved in the edit-error.

       """
    mis='^'+tup[0]
    tru='^'+tup[1]
    lst=recGetMistake(mis,1,tru,1,0)
    return lst


def recGetMistake(misake,mi,word,wi,i):
    """ Get the mistake types of by Levinstein of a tupple.

       Args:
           mistake (str): string with an edit error\s.
           mi (int): a position of the algorithm in mistake word.
           word (str): the correct word of the mistake.
           wi (int): a position of the algorithm in correct word.
           i (int): the number of mistakes till now.

       Returns:
           list of tupples , each tupple has a key of an edit-type-error string and value of the tow characters involved in the edit-error.

       """
    mis=misake[mi:]
    tru=word[wi:]
    if i>MAX_MISTAKES_IN_WORD :
        return []
    elif len(mis)==len(tru)==0:
        return []
    elif mis=="":
            res=[(Deletion,(word[wi-1],tru[0]))]
            for c in tru[1:]:
                res.append((Deletion,(c,'$')))
            return res
    elif tru=="":
            res = [(Insertion,(misake[-1],mis[0]))]
            for c in mis[1:]:
                res.append((Insertion, ('$', c)))
            return res
    elif mis[0]==tru[0]:
            return recGetMistake(misake,mi+1,word,wi+1,i)
    else:
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


def initCountDict(countDict):
    """ Initiates a dictionary of str,count.

       Args:
           countDict (dict): a dictionary you want to initiate with 1 for each combination in the alphabet.

       Returns:
           A dictionary initiated with 1 for each combination in the alphabet.

       """
    alphabet='abcdefghijklmnopqrstuvwxyz\x20\x27\x5e\x24'
    for i in alphabet:
        for j in alphabet:
            countDict[(i,j)]=1
    return countDict


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
    initCountDict(charactersCountDict)
    for dct in mistakesCountDict.keys():
        initCountDict(mistakesCountDict[dct])


    f=open(errors_file,'r',encoding='utf8')
    wholeFile=f.read().encode('utf8')
    f.close()
    wholeFile = normalizeText(wholeFile)
    separated = errFileToTupleList(wholeFile)

    for tup in separated:
        errTups=getMistake(tup)
        for curr in errTups:
            errTup=curr[1]
            errType=curr[0]
            insertToCountDict(errTup, mistakesCountDict[errType])
    for word in lexicon.keys():
        for c in word:
            insertToCountDict(c, charactersCountDict)
        for i in range(len(word)-1):
            c=word[i]+word[i+1]
            insertToCountDict(c, charactersCountDict)
    for etype in mistakesCountDict.keys():
        for tup in mistakesCountDict[etype]:
            p=calculateProbability(etype,tup[0],tup[1],mistakesCountDict,charactersCountDict)
            mistakesProbDict[etype][tup]=p
    return mistakesProbDict


def normalizeText(text):
    """ Removes any character not in [a-zA-Z\x20\x3e\x2d\n]

        Args:
            text (str): string of a long text.

        Returns:
            A normalized string to work with.

        """
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\x20\x3e\x2d\n]', "", text)
    text = text.split('\n')
    return text


def errFileToTupleList(wholeFile):
    """ parses an error file based on wikipedia file

        Args:
            wholeFile (str): string of a file based on (word1->word2\n)+ pattern.

        Returns:
            A list of tupples str,str of the two words around the '->'.

        """
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


def insertToCountDict(key, countDict):
    """ Increment a value in a dictionary

          Args:
              key (str): the string-key which value you want to increase.
              countDict (dict): a dictionary of str,int

          """
    if key in countDict:
        countDict[key] += 1
    else:
        countDict[key] = 1
# endregion

#region correct_word
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
    candidates,nothing = getCandidates(errors_dist, w, word_counts)
    best=None
    for c in candidates.keys():
        if best==None:
            best=c
        elif candidates[c]>candidates[best]:
            best=c
    return best


def getCandidates(errors_dist, w, word_counts,NUMBER_OF_CANDIDATES=5):
    """ gets a candidates of one word based on the noisy channel model.

          Args:
              errors_dist (dict): a dictionary of {str:dict} representing the error
                            distribution of each error type (as returned by
                            create_error_distribution() ).
              w (str): a word to correct
              word_counts (dict): a dictionary of {str:count} containing the
                            counts  of uniqie words (from previously loaded
                             corpora).
              NUMBER_OF_CANDIDATES (str): max number of candidates.

          Returns:
              returns a list of candidates of w and a list of edit-distances of these words.

          """
    candidates = dict()
    misCount=dict()
    CountOfAllWords=sum(word_counts.values())
    for word, count in word_counts.items():
        mis = getMistake((w, word))
        if (len(mis) < MAX_MISTAKES_IN_WORD):
            prob = 1
            for m in mis:
                prob *= errors_dist[m[0]][m[1]] * count/CountOfAllWords
            candidates[word] = prob
            misCount[word] = len(mis)
            if len(candidates)>NUMBER_OF_CANDIDATES:
                mn=min(candidates,key=candidates.get)
                del candidates[mn]
                del misCount[mn]
    return candidates,misCount


#endregion

#region generate_text



def reverseLm(lm):
    distributedBagOfWords=dict()
    for k,v in lm.items():
        for grm,c in v.items():
            for i in range(c):
                bow= grm.strip().split()
                bow.append(k.strip())
                if bow[0] not in distributedBagOfWords:
                    distributedBagOfWords[bow[0]] = dict()
                val=' '.join(bow[1:])
                if val !='' and val != ' ':
                    insertToCountDict(' '.join(bow[1:]), distributedBagOfWords[bow[0]])
    return distributedBagOfWords

def weightedRandom(reverselm,w):
    if w==None or w not in reverselm.keys():
        return choice(list(reverselm.keys()))
    wdct=reverselm[w]
    words=[]
    for k,count in wdct.items():
        for i in range(count):
            words.append(k)
    return choice(words)

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
    distBoW= reverseLm(lm)
    sentence=[]
    if w==None:
        w=choice(list(distBoW.keys()))
    sentence.append(w)
    while len(sentence) <m:
        last=sentence[-1]
        sentence+=weightedRandom(distBoW,last).split()
    return ' '.join(sentence[0:m])




#endregion  #

#region evaluate_text



def getSizeOfLM(lm):
    """ Returns the number of words in the text which the lm built from.

      Args:
          lm (dict): the language model to evaluate the sentence by.
      Returns:
          Number of words in the text that the lm was built from.
      """
    counter=10
    n=1
    for k0 in lm.keys():
        for k1 in lm[k0].keys():
            sz=len(k1.split())
            if sz>n :
                n=sz
        counter-=1
        if counter<=0:
            break
    return n+1


def evaluate_text(s,lm):
    """ Returns the likelihood of the specified sentence to be generated by the
    the specified language model.

    Args:
        s (str): the sentence to evaluate.
        lm (dict): the language model to evaluate the sentence by.
    Returns:
        The likelihood of the sentence according to the language model (float).
    """
    n=getSizeOfLM(lm)
    slm=learn_lm_from_string(s, n,None)
    res=1.0
    for k,v in slm.items():
        if k in lm.keys():
            for grm in v.keys():
                if grm in lm[k].keys():
                    res*=v[grm]
            counter = 1  ##smoothing
            for k in lm.values():
                if grm in k.keys():
                    counter += k[grm]
            res/=counter
    return res




#endregion

#region correct_sentence

def getWordCount(lm):
    """ Returns a dictionary of lexicon.

    Args:
        lm (dict): the language model built by the text.
    Returns:
        A dictionary of str,int any word in the model and the nu,ber of times it appears in the text.
    """
    wc=dict()
    for k,v in lm.items():
        for grm,count in v.items():
            for i in range(count):
                insertToCountDict(k, wc)
                for g in grm.split():
                    insertToCountDict(g, wc)
    return wc



def getCandidateSentences(candidateWords, c):
    """ Returns all candidate sentences with total edit distance of c.

    Args:
        candidateWords (list): a list of lists of tuppels. each tupple has 3 values (word,edit_distance, noisy channel probability), max edit-distance.
    Returns:
        A list of candidates with max edit-distance of c.
    """
    res=[]
    sentences=candidateWords[0]
    del candidateWords[0]
    while len(candidateWords)>0:
        sentences=list(product(sentences,candidateWords[0]))
        for i in range(len(sentences)):
            sentences[i]=(sentences[i][0][0]+' '+sentences[i][1][0],sentences[i][0][1]+sentences[i][1][1],sentences[i][0][2]+sentences[i][1][2])
        del candidateWords[0]
    for s in sentences:
        if s[1]<=c:
            res.append(s)
            if len(res) > 10:
                mn=min(res,key=lambda x:x[1])
                res.remove(mn)
    return res


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
    wc=getWordCount(lm)
    sentence=[]
    candidateWords=dict()
    candWordList=[]
    for st in linsplitter(s):
        sentence+=st.split()
    for w in sentence:
        candidateWords[w]=[]
    for w in sentence:
        candidates,misCount=getCandidates(err_dist,w,wc)
        candidates[w]=alpha
        misCount[w]=0
        for cand,p in candidates.items():
            if misCount[cand]<=c:
                candidateWords[w].append((cand,misCount[cand],p))
    for w in sentence:
        lst=[]
        for cand in candidateWords[w]:
            lst.append(cand)
        candWordList.append(lst)

    sentences=getCandidateSentences(candWordList,c)
    sentence=("",0)
    for s in sentences:
        etp=(s[0],evaluate_text(s[0],lm)*s[1])
        if etp[1]>sentence[1]:
            sentence=etp
    return sentence[0]


#endregion

#region testing

t1 = time.time()
print(t1)

#lexpath=r'/Users/toliks/Desktop/trump_historical_tweets.txt'
lexpath=r'/Users/toliks/Desktop/big.txt'
path=r'/Users/toliks/Desktop/wikipedia_common_misspellings.txt'

def getDistributedWords(lexpath):
    """ Returns a dictionary of lexicon.

    Args:
        s (str): the sentence to evaluate.
        lm (dict): the language model to evaluate the sentence by.
    Returns:
        The likelihood of the sentence according to the language model (float).
    """
    lm=learn_language_model(lexpath,n=1)
    words=dict()
    for word in lm.keys():
        words[word]=lm[word][""]
    return words

def dumpDicts():
    lm = learn_language_model([lexpath], n=3)
    flm = open(r'/Users/toliks/Desktop/flm.bin', 'wb')
    dump(lm, flm)
    flm.close()
    lex = getDistributedWords([lexpath])
    flex = open(r'/Users/toliks/Desktop/lex.bin', 'wb')
    dump(lex, flex)
    flex.close()
    ed = create_error_distribution(path, lex)
    fed = open(r'/Users/toliks/Desktop/fed.bin', 'wb')
    dump(ed, fed)
    fed.close()


def loadDicts():
    flex = open(r'/Users/toliks/Desktop/lex.bin', 'rb')
    lex=load(flex)
    flex.close()
    fed = open(r'/Users/toliks/Desktop/fed.bin', 'rb')
    ed=load(fed)
    fed.close()
    flm = open(r'/Users/toliks/Desktop/flm.bin', 'rb')
    lm = load(flm)
    flm.close()
    return lex,ed,lm
#dumpDicts()

lex,ed,lm=loadDicts()

#lex = getDistributedWords([lexpath])
#ed=create_error_distribution(path,lex)
#
t=correct_sentence('kill all of the stupid fanatics',lm,ed)
z=generate_text(lm,30)
k=0
print(t)
print(z)
#endregion