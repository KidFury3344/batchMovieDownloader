from bs4 import BeautifulSoup
import requests
import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox


headers = {'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'}

def getMovieNameYear(roughName):
    name = roughName.replace(" ", "-").lower()
    tmdbUrl = f"https://www.themoviedb.org/search?query={name}"
    request = requests.get(tmdbUrl, headers=headers)
    soup = BeautifulSoup(request.content,"lxml")
    searchResults = soup.find(class_="title")
    if searchResults:
        if searchResults.span != None:
            movieName = searchResults.a.get_text()
            movieYear = searchResults.span.get_text()
        else:
            try:
                searchResults = searchResults.find_next(class_="title")
                movieName = searchResults.a.get_text()
                movieYear = searchResults.span.get_text()
            except:
                error.set(f"{name} Not Found On TMDB")
                return [f"{name}", 0]
        movieYear = movieYear[-4:]
        return [movieName, movieYear]
    else:
        name = roughName.replace("-", " ").title()
        error.set(f"{name} Not Found On TMDB")
        return [f"{name}", 0]

def getMovieTorrentLinks(name, date):
    if " " in name:
        name = name.replace(" ", "%20")
    ytsSearchUrl = f"https://yts.mx/browse-movies/{name}/all/all/0/latest/{date}/all"
    request = requests.get(ytsSearchUrl, headers=headers)
    soup = BeautifulSoup(request.content, "lxml")
    movieTitle = soup.find(class_="browse-movie-title")
    if movieTitle:
        movieLink = movieTitle.get("href")
        requestTorrent = requests.get(movieLink, headers=headers)
        torrentSoup = BeautifulSoup(requestTorrent.content, "lxml")
        bottomInfo = torrentSoup.find(class_ = "bottom-info")
        bottomInfo = bottomInfo.p
        downloadLinks = bottomInfo.find_all("a")
        downloadDict = {}
        for results in downloadLinks:
            quality = results.get_text()
            link = results.get("href")
            downloadDict[quality] = link
        return downloadDict
    else:
        name = name.replace("%20", " ").title()
        error.set(f"{name} Not Found On YTS")
        return {f"{name}": 0}

def browseFiles():
    filename = filedialog.askopenfilename(initialdir = "/", title = "Select the text file containing movie names",filetypes =[("Text Files", "*.txt")])
    pathToFile_Entry.insert(0,filename)

def getMovieList(pathToFile, movieNames):
    if not pathToFile:
        movieNames = movieNames.replace(",", "\n")
        contents =  movieNames.strip() 
        movieList = []
        movieList = contents.split("\n")
        while "" in movieList:
            movieList.remove("")
        return movieList
    else:
        with open(pathToFile) as f:
            contents = f.read()
        movieNames = movieNames.replace(",", "")
        contents = contents.strip() + "\n" + movieNames.strip() 
        movieList = []
        movieList = contents.split("\n")
        while "" in movieList:
            movieList.remove("")
        return movieList

def aria2Download(path, linkFile):
    command = f'aria2c -d "{path}" -j 4 -i "{linkFile}" --seed-time=0 rpc-save-upload-metadata=false continue=true allow-overwrite=true bt-save-metadata=false seed-ratio=0'
    os.system(command)

def execute():
    pathFile = pathToFile.get()
    if pathFile:
        pathDir = os.path.dirname(pathFile)
    else:
        pathDir="."
    movies = movieNames.get()
    choice = choose.get()
    if choice == "0":
        error.set("Please Select Which Quality Torrent You Want")
    elif (pathFile or movies) and choice != 0:
        movieList = getMovieList(pathFile, movies)
        linkList = []
        failList =[]
        namelist = []
        for movie in movieList:
            nameDate = getMovieNameYear(movie)
            if nameDate[1] != 0:
                namelist.append(nameDate[0])
                quality = choice
                links = getMovieTorrentLinks(nameDate[0],nameDate[1])
                if quality == "1080p":
                    try:
                        linkList.append(links[f"{quality}.BluRay"])
                        linkList.append("\n")
                    except KeyError:
                        linkList.append(links[f"{quality}.WEB"])
                        linkList.append("\n")
                elif quality == "720p":
                    try:
                        linkList.append(links[f"{quality}.BluRay"])
                        linkList.append("\n")
                    except KeyError:
                        linkList.append(links[f"{quality}.WEB"])
                        linkList.append("\n")
            else:
                failList.append(f"#{nameDate[0]} Not Found On TMDb")
                failList.append("\n")
        path = writeToFile(linkList, pathDir, failList)
        if check.get() == 1:
            root.iconify()
            aria2Download(pathDir, path)
            pathDir = os.path.realpath(pathDir)
            done(f"\nMovies Downloaded to {pathDir}")
        elif check.get() == 2:
            getTorrents(linkList,namelist)
            pathDir = os.path.realpath(pathDir)
            done(f"\n Torrent Files Saved to {pathDir}")

    else:
        error.set("No Path Or Movie Name Found")
    


def writeToFile(linkList, pathToDir, failList):
    with open(pathToDir+r"\Output.txt", "w") as f:
        f.writelines(linkList)
        f.writelines(failList)
    return pathToDir+r"/Output.txt"

def getTorrents(linkList, nameList):
    while "\n" in linkList:
        linkList.remove("\n")
    print(linkList)
    for i in range(len(linkList)):
        with open(f"{nameList[i]}.torrent", "wb") as f:
            f.write(requests.get(linkList[i]).content)


def done(outputMessage):
    return messagebox.showinfo(title=f"Done", detail=f'Your Task Has Been Completed.{outputMessage}', parent=mainframe)

root = Tk()
root.title("Batch Movie Downloader")

mainframe = ttk.Frame(root) 
mainframe.grid(column=0, row=0)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
movieNames = StringVar()
movieName_Label = ttk.Label(mainframe, text="Enter Movies Comma Seperated: ").grid(column=0, row=1, sticky=(N,S,E,W))
orLabel = ttk.Label(mainframe, text="Enter Path to File Or").grid(column=0, row=2, sticky=(N,S,E,W))
movieName_entry = ttk.Entry(mainframe, width=50, textvariable=movieNames)
movieName_entry.grid(column=3, row=1, sticky=(N,S,E,W))
movieName_entry.focus()
pathToFile = StringVar()
pathToFile_Entry = ttk.Entry(mainframe, width=50, textvariable=pathToFile)
pathToFile_Entry.grid(column=3, row=2 ,sticky=(N,S,E,W))
chooseFile = ttk.Button(mainframe, text="Choose File", command=browseFiles).grid(column=2, row=2, sticky=(N, S, W, E))
getLink = ttk.Button(mainframe, text="Execute", command=execute).grid(column=3, row=3,rowspan=2, sticky=(N, S, W, E))

error = StringVar()
errorPrompt = ttk.Label(mainframe,width=100, textvariable=error, foreground="red")
choose = StringVar(value="0")
seven20 = ttk.Radiobutton(mainframe, text="720p", variable=choose, value = "720p").grid(column=0, row=3, sticky=(W, E))
ten80 = ttk.Radiobutton(mainframe, text="1080p", variable=choose, value = "1080p").grid(column=0, row=4, sticky=(W, E))

check = IntVar()
AriaCheck = ttk.Checkbutton(mainframe, text="Aria2c In Environment Path", variable=check, onvalue=1).grid(column= 0, row=5, sticky=(W,E))
downloadTorrent = ttk.Checkbutton(mainframe, text="Download Torrent Files", variable=check, onvalue=2).grid(column= 0, row=6, sticky=(W,E))
check.set(0)


for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

root.mainloop()

