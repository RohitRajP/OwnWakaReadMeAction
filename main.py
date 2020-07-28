# https://foobar.withgoogle.com/
# access token - 225d0880663641cd5db98dfe2dde2efd3a6be6f2

import re
import os
import base64
import sys
import datetime
import requests
from github import Github, GithubException

# marks the readME markers to insert data into
START_COMMENT_LANGUAGE = '<!--START_SECTION:waka-->'
END_COMMENT_LANGUAGE = '<!--END_SECTION:waka-->'
START_COMMENT_PROJECT = '<!--START_SECTION:wakaproj-->'
END_COMMENT_PROJECT = '<!--END_SECTION:wakaproj-->'
# regular expressions for the readme markers
listRegLang = f"{START_COMMENT_LANGUAGE}[\\s\\S]+{END_COMMENT_LANGUAGE}"
listRegProj = f"{START_COMMENT_PROJECT}[\\s\\S]+{END_COMMENT_PROJECT}"

# getting the API response for the API Key
def getAPIResponse(wakaApiKey):
    try:
        # sendinf request to API (f used to replace value for wakaApiKey)
        return requests.get(f"https://wakatime.com/api/v1/users/current/stats/last_7_days?api_key={wakaApiKey}").json()
    except:
        print("Exception in getAPIResponse()")

# parsing required data from the recieved response
def parseRequiredData(apiResponseData):
    try:
        # getting languages and projects data
        languagesData = apiResponseData["data"]["languages"]
        projectData = apiResponseData["data"]["projects"]

        # lists to hold the required values dictionaries
        languagesLists = []
        projectsLists = []

        # iterating through all language data
        for language in languagesData:
            # getting required data from the language object
            languagesLists.append({
                "name":language["name"],
                "percent":round(language["percent"])
            }.copy())

        # iterating through all the project data
        for project in projectData:
            # getting required data from the project object
            projectsLists.append({
                "name":project["name"],
                "percent":round(project["percent"])
            }.copy())

        return [languagesLists,projectsLists]
    except:
        print("Exception in parseRequiredData")

# construct graphs for each parsed data
def constuctGraphs(parsedData):
    try:
        # specifying graph blocks
        done_block = '█'
        empty_block = '░'

        # dicts to hold the graph strings
        langGraphStrings = {}
        projectGraphStrings = {}

        # iterating through language data
        for languageData in parsedData[0]:
            # getting required values
            percentVal = languageData["percent"]
            # adding graph to the list
            langGraphStrings[languageData["name"]] = f"{done_block*int(percentVal/4)}{empty_block*int(25-int(percentVal/4))}"
        
        # iterating through projects data
        for projectData in parsedData[1]:
            # getting required values
            percentVal = projectData["percent"]
            # adding graph to the list
            projectGraphStrings[projectData["name"]] = f"{done_block*int(percentVal/4)}{empty_block*int(25-int(percentVal/4))}"

        return {
            "languagesData":{
                "graphs":langGraphStrings,
                "metaData":parsedData[0]
            },
            "projectsData":{
                "graphs":projectGraphStrings,
                "metaData":parsedData[1]
            }
        }
    except:
        print("Exception in constructGraphs()")

# returns week streak
def weekStreak():
    week_end = datetime.datetime.today() - datetime.timedelta(days=1)
    week_start = week_end - datetime.timedelta(days=7)
    return f"Week: {week_start.strftime('%d %B, %Y')} - {week_end.strftime('%d %B, %Y')}"

# construct the markdown text to insert into ReadME
def constructReadMEString(graphsData):
    try:
        # holds list of markdown strings
        languageMarkdownStrings = []
        projectMarkdownStrings = []

        # finding length of largest name
        maxLangNameLen = len(max([l['name'] for l in graphsData["languagesData"]["metaData"]], key=len))
        maxProjNameLen = len(max([l['name'] for l in graphsData["projectsData"]["metaData"]], key=len))

        # constructing language markdown string 
        for metaData in graphsData["languagesData"]["metaData"]:
            # getting data related to the language
            langName = metaData["name"]
            langGraph = graphsData["languagesData"]["graphs"][langName]
            langPercent = metaData["percent"]
            # appending string to list of strings
            languageMarkdownStrings.append(
                f"{langName}{' '*(maxLangNameLen - len(langName) + 3)}{langGraph}   {langPercent} %"
            )

        # constructing projects markdown string
        for metaData in graphsData["projectsData"]["metaData"]:
            # getting data related to the language
            projName = metaData["name"]
            projGraph = graphsData["projectsData"]["graphs"][projName]
            projPercent = metaData["percent"]
            # appending string to list of strings
            projectMarkdownStrings.append(
                f"{projName}{' '*(maxProjNameLen - len(projName) + 3)}{projGraph}   {projPercent} %"
            )

        return {
            "languageString":"\n".join(languageMarkdownStrings),
            "projectString":"\n".join(projectMarkdownStrings)
        }
    except:
        print("Exception in constructReadMEString()")

# decode the contents of old readme
def decode_readme(data):
    decoded_bytes = base64.b64decode(data)
    return str(decoded_bytes, 'utf-8')

# generate a new Readme.md
def generateNewReadme(readMeStrings, readMeFileDecoded): 

    # constructing final readMe strings
    languageMdString = '```text\n'+weekStreak()+'\n\n'+readMeStrings["languageString"]+'\n```'
    projectMdString = '```text\n'+weekStreak()+'\n\n'+readMeStrings["projectString"]+'\n```'

    # adding content between the flags
    languageReadMeStats = f"{START_COMMENT_LANGUAGE}\n{languageMdString}\n{END_COMMENT_LANGUAGE}"
    projectReadMeStats = f"{START_COMMENT_PROJECT}\n{projectMdString}\n{END_COMMENT_PROJECT}"
    return re.sub(listRegLang, languageReadMeStats, readMeFileDecoded), re.sub(listRegProj, projectReadMeStats, readMeFileDecoded)

# entrypoint of code execution
if __name__ == "__main__":
    try:

        # getting data from github 
        userName = os.getenv('INPUT_USERNAME')
        wakaApiKey = os.getenv('INPUT_WAKATIME_API_KEY')
        githubToken = os.getenv('INPUT_GH_TOKEN')
        
        # getting github instance
        githubInstance = Github(githubToken)

        try:
            # getting instance of required instance
            repo = githubInstance.get_repo(f"{userName}/{userName}")
        except GithubException:
            print("Authentication Error. Try saving a GitHub Token in your Repo Secrets or Use the GitHub Actions Token, which is automatically used by the action.")
            sys.exit(1)

        # getting the ReadMe file
        readMeFile = repo.get_readme()

        # decode the contents of old readme
        readMeFileDecoded = decode_readme(readMeFile.content)

        # getting the API response for the API Key
        apiResponseData = getAPIResponse(wakaApiKey)

        # parsing required data from the recieved response
        parsedData = parseRequiredData(apiResponseData)

        # construct graphs for the precent data for each parsed data type
        graphsData = constuctGraphs(parsedData)

        # construct the markdown text to insert into ReadME
        readMeStrings = constructReadMEString(graphsData)
        
        # generating new ReadMe files
        newReadmeLang, newReadmeProj = generateNewReadme(readMeStrings=readMeStrings, readMeFileDecoded=readMeFileDecoded)

        # updating readMeFiles
        repo.update_file(path=readMeFile.path, message='Updated LanguageStats', content=newReadmeLang, sha=readMeFile.sha, branch='master')
        repo.update_file(path=readMeFile.path, message='Updated ProjectStats', content=newReadmeProj, sha=readMeFile.sha, branch='master')

    except:
        print("Exception in main()")


    

    

    
