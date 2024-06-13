import threading
import crawlers.nobel_crawler as nobel_crawler
import crawlers.submarino_crawler as submarino_crawler
import crawlers.curitiba_crawler as curitiba_crawler
import crawlers.cultura_crawler as cultura_crawler
import merger as merger
import graph as grapher

threads = []

#threads.append(threading.Thread(target=nobel_crawler.run))
#threads.append(threading.Thread(target=submarino_crawler.run))
#threads.append(threading.Thread(target=curitiba_crawler.run))
#threads.append(threading.Thread(target=cultura_crawler.run))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

merger.run()
grapher.run()

print("Finished processing")
