import chainlit as cl
import requests
import json

class TextbookInfoRetriever:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'authorization': 'wixcode-pub.18385fb311792b7a2cd1f9c7d69d21ac6e1417fc.eyJpbnN0YW5jZUlkIjoiMDUzZDZjZjgtYzM1Yi00MWI3LTk4ZDItNTkwMWQ4YjM0NmI5IiwiaHRtbFNpdGVJZCI6ImM2ZThlNTM2LWY4NDEtNGYwMi05NWNhLTgyNmRjYzczNzA3MCIsInVpZCI6bnVsbCwicGVybWlzc2lvbnMiOm51bGwsImlzVGVtcGxhdGUiOmZhbHNlLCJzaWduRGF0ZSI6MTY5NTQwMDMzOTI4MiwiYWlkIjoiMjZmNjg1NDMtMTg2Ny00MTU2LTk3ZmEtMjg0ZDdiMTc5MzdiIiwiYXBwRGVmSWQiOiJDbG91ZFNpdGVFeHRlbnNpb24iLCJpc0FkbWluIjpmYWxzZSwibWV0YVNpdGVJZCI6IjNkYjk3OTJmLTliYWYtNDg0Ny05ZGIxLWI2ZDVjYzc5YWIwZiIsImNhY2hlIjpudWxsLCJleHBpcmF0aW9uRGF0ZSI6bnVsbCwicHJlbWl1bUFzc2V0cyI6IlNob3dXaXhXaGlsZUxvYWRpbmcsSGFzRG9tYWluLEFkc0ZyZWUiLCJ0ZW5hbnQiOm51bGwsInNpdGVPd25lcklkIjoiNzNkZmY5YmMtZDRjNy00YjQ2LTg1OTEtNTM0YzBkNmFlYjE1IiwiaW5zdGFuY2VUeXBlIjoicHViIiwic2l0ZU1lbWJlcklkIjpudWxsLCJwZXJtaXNzaW9uU2NvcGUiOm51bGwsImxvZ2luQWNjb3VudElkIjpudWxsLCJpc0xvZ2luQWNjb3VudE93bmVyIjpudWxsfQ==',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.litsolutions.org/_partials/wix-thunderbolt/dist/clientWorker.b151dd12.bundle.min.js',
            'commonConfig': '%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22BSI%22%3A%221ddd14da-29be-45c5-92f6-53a98832da67%7C10%22%7D',
            'x-wix-brand': 'wix',
            'X-Wix-Client-Artifact-Id': 'wix-thunderbolt', 
        }
        self.names = ['RQ', 'P', 'E', 'SP','CQ','CRCT','MCQ','QP','WWQ','CTQ','QP', 'PE']
        self.p = 1
        self.found = False
        self.m = None
        self.book = None
        self.chapter = None
        self.question = None

    async def retrieve_textbook_info(self, book, chapter, question):
        self.book = book
        self.chapter = chapter
        self.question = question
        for i in range(1, 33):
            json_data = {
                'collectionName': f'dsd{self.p}',
                'dataQuery': {
                    'filter': {
                        '$and': [
                            {'bookName': {'$contains': self.book}},
                            {'fileName': {'$contains': f'Chapter {str(self.chapter)},'}},
                        ],
                    },
                    'paging': {'offset': 0},
                    'fields': [],
                },
                'options': {},
                'includeReferencedItems': [],
                'segment': 'LIVE',
                'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
            }

            response = requests.post(
                'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
                headers=self.headers,
                json=json_data,
            )

            print(response.status_code)

            self.m = json.loads(response.text)
            print(self.m)

            if 'items' in self.m and len(self.m['items']) > 1:
                self.found = await self.handle_user_response(self.book, self.chapter, self.question)
                if self.found:
                    break

            self.p += 1
            print(self.p)

    async def handle_user_response(self, book, chapter, question):
        msg = await cl.AskUserMessage(
            content=f'Is this the textbook you specified: {self.m["items"][0]["bookName"]}',
            timeout=60,
        ).send()
        self.book = self.m["items"][0]["bookName"]
        print(msg)

        await self.direction(msg)

    async def direction(self, msg):
        if msg and 'output' in msg:
            r = msg['output']
        if r == 'y' or r == 'yes' or r == 'Y' or r == 'Yeah' or r == 'Yes':
            return await self.handle_yes_response(self.book, self.chapter, self.question)
        else:
            await cl.Message(content='Please specify the textbook name again, but be more specific with respect to the textbook official name').send()
            return False

    async def handle_yes_response(self, book, chapter, question):
        print("Handling yes response...")
        print("Book:", book)
        print("Chapter:", chapter)
        print("Question:", question)
        
        for item in self.m['items']:
            print("Checking item:", item)
            if book in item['bookName']:
                print("Book name matched")
                for i in self.names:
                    # print("Checking name:", i)
                    problem = f'{question}{i}'
                    print(problem)
                    if item['problem'] == problem and (item['chapter'] == chapter or item['problem'] == question):
                        print("Problem and chapter matched")
                        link = item['link']
                        await cl.Message(content=f'Chapter found: {item["chapter"]}').send()
                        print("Link:", link)
                        await cl.Message(content=f'Here is the guide to the solution to question {question}: {link}').send()
                        return True
            else:
                print("Problem or chapter mismatch")
                await cl.Message(content=f'There seems to be a problem, please try again').send()
        
        print("No matching item found")
        return False






# import chainlit as cl
# import requests
# import json

# class TextbookInfoRetriever:
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
#             'authorization': 'wixcode-pub.18385fb311792b7a2cd1f9c7d69d21ac6e1417fc.eyJpbnN0YW5jZUlkIjoiMDUzZDZjZjgtYzM1Yi00MWI3LTk4ZDItNTkwMWQ4YjM0NmI5IiwiaHRtbFNpdGVJZCI6ImM2ZThlNTM2LWY4NDEtNGYwMi05NWNhLTgyNmRjYzczNzA3MCIsInVpZCI6bnVsbCwicGVybWlzc2lvbnMiOm51bGwsImlzVGVtcGxhdGUiOmZhbHNlLCJzaWduRGF0ZSI6MTY5NTQwMDMzOTI4MiwiYWlkIjoiMjZmNjg1NDMtMTg2Ny00MTU2LTk3ZmEtMjg0ZDdiMTc5MzdiIiwiYXBwRGVmSWQiOiJDbG91ZFNpdGVFeHRlbnNpb24iLCJpc0FkbWluIjpmYWxzZSwibWV0YVNpdGVJZCI6IjNkYjk3OTJmLTliYWYtNDg0Ny05ZGIxLWI2ZDVjYzc5YWIwZiIsImNhY2hlIjpudWxsLCJleHBpcmF0aW9uRGF0ZSI6bnVsbCwicHJlbWl1bUFzc2V0cyI6IlNob3dXaXhXaGlsZUxvYWRpbmcsSGFzRG9tYWluLEFkc0ZyZWUiLCJ0ZW5hbnQiOm51bGwsInNpdGVPd25lcklkIjoiNzNkZmY5YmMtZDRjNy00YjQ2LTg1OTEtNTM0YzBkNmFlYjE1IiwiaW5zdGFuY2VUeXBlIjoicHViIiwic2l0ZU1lbWJlcklkIjpudWxsLCJwZXJtaXNzaW9uU2NvcGUiOm51bGwsImxvZ2luQWNjb3VudElkIjpudWxsLCJpc0xvZ2luQWNjb3VudE93bmVyIjpudWxsfQ==',
#             'Content-Type': 'application/json',
#             'Accept': 'application/json, text/plain, */*',
#             'Referer': 'https://www.litsolutions.org/_partials/wix-thunderbolt/dist/clientWorker.b151dd12.bundle.min.js',
#             'commonConfig': '%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22BSI%22%3A%221ddd14da-29be-45c5-92f6-53a98832da67%7C10%22%7D',
#             'x-wix-brand': 'wix',
#             'X-Wix-Client-Artifact-Id': 'wix-thunderbolt', 
#         }
#         self.names = ['RQ', 'P', 'E', 'SP']
#         self.p = 1
#         self.found = False
#         self.m = None

#     def retrieve_textbook_info(self, book, chapter, question):
#         while True:
#             json_data = {
#                 'collectionName': f'dsd{self.p}',
#                 'dataQuery': {
#                     'filter': {
#                         '$and': [
#                             {'bookName': {'$contains': book}},
#                             {'fileName': {'$contains': f'Chapter {chapter}'}},
#                         ],
#                     },
#                     'paging': {'offset': 0},
#                     'fields': [],
#                 },
#                 'options': {},
#                 'includeReferencedItems': [],
#                 'segment': 'LIVE',
#                 'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
#             }

#             response = requests.post(
#                 'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
#                 headers=self.headers,
#                 json=json_data,
#             )
#             print(response.status_code)

#             self.m = json.loads(response.text)
#             print(self.m)

#             if 'items' in self.m and len(self.m['items']) > 1:
#                 self.found = self.handle_user_response(book, chapter, question)
#                 if self.found:
#                     break

#             self.p += 1
#             print(self.p)

#     def handle_user_response(self, book, chapter, question):
#         actions = [
#             cl.Action(name="yes_button", value="yes", label="Yes"),
#             cl.Action(name="no_button", value="no", label="No")
#         ]

#         msg = cl.Message(
#             content=f'Is this the textbook you specified: {self.m["items"][0]["bookName"]}',
#             actions=actions,
#         ).send()

#         user_input = input("Y or N: ").lower()

#         if user_input == 'y' or user_input == 'yes':
#             return self.handle_yes_response(book, chapter, question)
#         elif user_input == 'n' or user_input == 'no':
#             print('Please specify the textbook name again, but be more specific with respect to the textbook official name')
#             return False

#     def handle_yes_response(self, book, chapter, question):
#         for item in self.m['items']:
#             if book in item['bookName']:
#                 for i in self.names:
#                     problem = f'{question}{i}'
#                     if item['problem'] == problem and (item['chapter'] == chapter or item['problem'] == question):
#                         cl.Message(content=f'Chapter found: {item["chapter"]}').send()
#                         link = item['link']
#                         cl.Message(content=f'Here is the guide to the solution to question {question}').send()
#                         cl.Message(content=f'Here is the guide to the solution to question {link}').send()
#                         return link
#         print("Sorry, couldn't find the information you requested.")
#         return None











# import requests
# import json

# class TextbookInfoRetriever:
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
#             'authorization': 'wixcode-pub.18385fb311792b7a2cd1f9c7d69d21ac6e1417fc.eyJpbnN0YW5jZUlkIjoiMDUzZDZjZjgtYzM1Yi00MWI3LTk4ZDItNTkwMWQ4YjM0NmI5IiwiaHRtbFNpdGVJZCI6ImM2ZThlNTM2LWY4NDEtNGYwMi05NWNhLTgyNmRjYzczNzA3MCIsInVpZCI6bnVsbCwicGVybWlzc2lvbnMiOm51bGwsImlzVGVtcGxhdGUiOmZhbHNlLCJzaWduRGF0ZSI6MTY5NTQwMDMzOTI4MiwiYWlkIjoiMjZmNjg1NDMtMTg2Ny00MTU2LTk3ZmEtMjg0ZDdiMTc5MzdiIiwiYXBwRGVmSWQiOiJDbG91ZFNpdGVFeHRlbnNpb24iLCJpc0FkbWluIjpmYWxzZSwibWV0YVNpdGVJZCI6IjNkYjk3OTJmLTliYWYtNDg0Ny05ZGIxLWI2ZDVjYzc5YWIwZiIsImNhY2hlIjpudWxsLCJleHBpcmF0aW9uRGF0ZSI6bnVsbCwicHJlbWl1bUFzc2V0cyI6IlNob3dXaXhXaGlsZUxvYWRpbmcsSGFzRG9tYWluLEFkc0ZyZWUiLCJ0ZW5hbnQiOm51bGwsInNpdGVPd25lcklkIjoiNzNkZmY5YmMtZDRjNy00YjQ2LTg1OTEtNTM0YzBkNmFlYjE1IiwiaW5zdGFuY2VUeXBlIjoicHViIiwic2l0ZU1lbWJlcklkIjpudWxsLCJwZXJtaXNzaW9uU2NvcGUiOm51bGwsImxvZ2luQWNjb3VudElkIjpudWxsLCJpc0xvZ2luQWNjb3VudE93bmVyIjpudWxsfQ==',
#             'Content-Type': 'application/json',
#             'Accept': 'application/json, text/plain, */*',
#             'Referer': 'https://www.litsolutions.org/_partials/wix-thunderbolt/dist/clientWorker.b151dd12.bundle.min.js',
#             'commonConfig': '%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22BSI%22%3A%221ddd14da-29be-45c5-92f6-53a98832da67%7C10%22%7D',
#             'x-wix-brand': 'wix',
#             'X-Wix-Client-Artifact-Id': 'wix-thunderbolt', 
#         }
#         self.names = ['RQ', 'P', 'E', 'SP']
#         self.p = 1
#         self.found = False
#         self.m = None

#     def retrieve_textbook_info(self, book, chapter, question):
#         while True:
#             json_data = {
#                 'collectionName': f'dsd{self.p}',
#                 'dataQuery': {
#                     'filter': {
#                         '$and': [
#                             {'bookName': {'$contains': book}},
#                             {'fileName': {'$contains': f'Chapter {chapter}'}},
#                         ],
#                     },
#                     'paging': {'offset': 0},
#                     'fields': [],
#                 },
#                 'options': {},
#                 'includeReferencedItems': [],
#                 'segment': 'LIVE',
#                 'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
#             }

#             response = requests.post(
#                 'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
#                 headers=self.headers,
#                 json=json_data,
#             )
#             print(response.status_code)

#             self.m = json.loads(response.text)
#             print(self.m)

#             if 'items' in self.m and len(self.m['items']) > 1:
#                 self.found = self.handle_user_response(book, chapter, question)
#                 if self.found:
#                     break

#             self.p += 1
#             print(self.p)

#     def handle_user_response(self, book, chapter, question):
#         print(f'Is this the textbook you specified: {self.m["items"][0]["bookName"]}')
#         resp = input("Y or N: ").lower()

#         if resp == 'y' or resp == 'yes':
#             return self.handle_yes_response(book, chapter, question)
#         elif resp == 'n' or resp == 'no':
#             print('Please specify the textbook name again, but be more specific with respect to the textbook official name')
#             return False

#     def handle_yes_response(self, book, chapter, question):
#         for item in self.m['items']:
#             if book in item['bookName']:
#                 for i in self.names:
#                     problem = f'{question}{i}'
#                     if item['problem'] == problem and (item['chapter'] == chapter or item['problem'] == question):
#                         print('Chapter found:', item['chapter'])
#                         print(f'Here is the guide to the solution to question {question}')
#                         link = item['link']
#                         return link
#         print("Sorry, couldn't find the information you requested.")
#         return None

# # Example usage:
# retriever = TextbookInfoRetriever()
# book_input = input('Book: ')
# chapter_input = input('Chapter: ')
# question_input = input('Question: ')


# retriever.retrieve_textbook_info(book_input, chapter_input, question_input)




# import requests
# import json


# class TextbookInfoRetriever:
#     def __init__(self):
#         self.m = None  # Initialize m to None

#     def get_textbook_info(self, book, chapter, question):
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
#             'authorization': 'wixcode-pub.18385fb311792b7a2cd1f9c7d69d21ac6e1417fc.eyJpbnN0YW5jZUlkIjoiMDUzZDZjZjgtYzM1Yi00MWI3LTk4ZDItNTkwMWQ4YjM0NmI5IiwiaHRtbFNpdGVJZCI6ImM2ZThlNTM2LWY4NDEtNGYwMi05NWNhLTgyNmRjYzczNzA3MCIsInVpZCI6bnVsbCwicGVybWlzc2lvbnMiOm51bGwsImlzVGVtcGxhdGUiOmZhbHNlLCJzaWduRGF0ZSI6MTY5NTQwMDMzOTI4MiwiYWlkIjoiMjZmNjg1NDMtMTg2Ny00MTU2LTk3ZmEtMjg0ZDdiMTc5MzdiIiwiYXBwRGVmSWQiOiJDbG91ZFNpdGVFeHRlbnNpb24iLCJpc0FkbWluIjpmYWxzZSwibWV0YVNpdGVJZCI6IjNkYjk3OTJmLTliYWYtNDg0Ny05ZGIxLWI2ZDVjYzc5YWIwZiIsImNhY2hlIjpudWxsLCJleHBpcmF0aW9uRGF0ZSI6bnVsbCwicHJlbWl1bUFzc2V0cyI6IlNob3dXaXhXaGlsZUxvYWRpbmcsSGFzRG9tYWluLEFkc0ZyZWUiLCJ0ZW5hbnQiOm51bGwsInNpdGVPd25lcklkIjoiNzNkZmY5YmMtZDRjNy00YjQ2LTg1OTEtNTM0YzBkNmFlYjE1IiwiaW5zdGFuY2VUeXBlIjoicHViIiwic2l0ZU1lbWJlcklkIjpudWxsLCJwZXJtaXNzaW9uU2NvcGUiOm51bGwsImxvZ2luQWNjb3VudElkIjpudWxsLCJpc0xvZ2luQWNjb3VudE93bmVyIjpudWxsfQ==',
#             'Content-Type': 'application/json',
#             'Accept': 'application/json, text/plain, */*',
#             'Referer': 'https://www.litsolutions.org/_partials/wix-thunderbolt/dist/clientWorker.b151dd12.bundle.min.js',
#             'commonConfig': '%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22BSI%22%3A%221ddd14da-29be-45c5-92f6-53a98832da67%7C10%22%7D',
#             'x-wix-brand': 'wix',
#             'X-Wix-Client-Artifact-Id': 'wix-thunderbolt', 
#         }

#         names = ['RQ', 'P', 'E', 'SP']
#         p = 1
#         found = False

#         while True:
#             json_data = {
#                 'collectionName': f'dsd{p}',
#                 'dataQuery': {
#                     'filter': {
#                         '$and': [
#                             {
#                                 'bookName': {
#                                     '$contains': book
#                                 },
#                                 'fileName': {
#                                     '$contains': f'Chapter {chapter}',
#                                 },
#                             },
#                         ],
#                     },
#                     'paging': {
#                         'offset': 0,
#                     },
#                     'fields': [],
#                 },
#                 'options': {},
#                 'includeReferencedItems': [],
#                 'segment': 'LIVE',
#                 'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
#             }

#             response = requests.post(
#                 'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
#                 headers=headers,
#                 json=json_data,
#             )
#             print(response.status_code)

#             try:
#                 self.m = json.loads(response.text)
#                 print(self.m)
#             except json.JSONDecodeError:
#                 print("Failed to decode JSON response.")
#                 break

#             if 'items' in self.m and len(self.m['items']) > 1:
#                 print(f'Is this the textbook you specified: {self.m["items"][0]["bookName"]}')
#                 resp = input("Y or N: ").lower()

#                 if resp == 'y' or resp == 'yes':
#                     found = self.handle_yes_response(book, chapter, question)
#                 elif resp == 'n' or resp == 'no':
#                     print('Please specify the textbook name again, but be more specific with respect to the textbook official name')
#                     break

#             if found:
#                 break
#             else:
#                 p += 1
#                 print(p)

#     def handle_yes_response(self, book, chapter, question):
#         names = ['RQ', 'P', 'E', 'SP']
#         for item in self.m['items']:
#             if book in item['bookName']:
#                 for i in names:
#                     problem = f'{question}{i}'
#                     if item['problem'] == problem and (item['chapter'] == chapter or item['problem'] == question):
#                         print('Chapter found:', item['chapter'])
#                         print(f'Here is the guide to the solution to question {question}')
#                         link = item['link']
#                         return link
#                         break
#                     else:
#                         continue
#         return None


# # Usage
# retriever = TextbookInfoRetriever()

# book_input = input('Book: ')
# chapter_input = input('Chapter: ')
# question_input = input('Question: ')


# retriever.get_textbook_info(book_input, chapter_input, question_input)



# import requests
# import json


# def get_textbook_info(book, chapter, question):
#     headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
#     'authorization': 'wixcode-pub.18385fb311792b7a2cd1f9c7d69d21ac6e1417fc.eyJpbnN0YW5jZUlkIjoiMDUzZDZjZjgtYzM1Yi00MWI3LTk4ZDItNTkwMWQ4YjM0NmI5IiwiaHRtbFNpdGVJZCI6ImM2ZThlNTM2LWY4NDEtNGYwMi05NWNhLTgyNmRjYzczNzA3MCIsInVpZCI6bnVsbCwicGVybWlzc2lvbnMiOm51bGwsImlzVGVtcGxhdGUiOmZhbHNlLCJzaWduRGF0ZSI6MTY5NTQwMDMzOTI4MiwiYWlkIjoiMjZmNjg1NDMtMTg2Ny00MTU2LTk3ZmEtMjg0ZDdiMTc5MzdiIiwiYXBwRGVmSWQiOiJDbG91ZFNpdGVFeHRlbnNpb24iLCJpc0FkbWluIjpmYWxzZSwibWV0YVNpdGVJZCI6IjNkYjk3OTJmLTliYWYtNDg0Ny05ZGIxLWI2ZDVjYzc5YWIwZiIsImNhY2hlIjpudWxsLCJleHBpcmF0aW9uRGF0ZSI6bnVsbCwicHJlbWl1bUFzc2V0cyI6IlNob3dXaXhXaGlsZUxvYWRpbmcsSGFzRG9tYWluLEFkc0ZyZWUiLCJ0ZW5hbnQiOm51bGwsInNpdGVPd25lcklkIjoiNzNkZmY5YmMtZDRjNy00YjQ2LTg1OTEtNTM0YzBkNmFlYjE1IiwiaW5zdGFuY2VUeXBlIjoicHViIiwic2l0ZU1lbWJlcklkIjpudWxsLCJwZXJtaXNzaW9uU2NvcGUiOm51bGwsImxvZ2luQWNjb3VudElkIjpudWxsLCJpc0xvZ2luQWNjb3VudE93bmVyIjpudWxsfQ==',
#     'Content-Type': 'application/json',
#     'Accept': 'application/json, text/plain, */*',
#     'Referer': 'https://www.litsolutions.org/_partials/wix-thunderbolt/dist/clientWorker.b151dd12.bundle.min.js',
#     'commonConfig': '%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22BSI%22%3A%221ddd14da-29be-45c5-92f6-53a98832da67%7C10%22%7D',
#     'x-wix-brand': 'wix',
#     'X-Wix-Client-Artifact-Id': 'wix-thunderbolt', 
#     }

#     names = ['RQ', 'P', 'E', 'SP']
#     p = 1
#     found = False


#     while True:
#         json_data = {
#             'collectionName': f'dsd{p}',
#             'dataQuery': {
#                 'filter': {
#                     '$and': [
#                         {
#                             'bookName': {
#                                 '$contains': book
#                             },
#                             'fileName': {
#                                 '$contains': f'Chapter {chapter}',
#                             },
#                         },
#                     ],
#                 },
#                 'paging': {
#                     'offset': 0,
#                 },
#                 'fields': [],
#             },
#             'options': {},
#             'includeReferencedItems': [],
#             'segment': 'LIVE',
#             'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
#         }

#         response = requests.post(
#             'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
#             headers=headers,
#             json=json_data,
#         )
#         print(response.status_code)

#         m = json.loads(response.text)
#         print(m)

#         if len(m['items']) > 1:
#             print(f'Is this the textbook you specified: {m["items"][0]["bookName"]}')
#             resp = input("Y or N: ").lower()

#             if resp == 'y' or resp == 'yes':
#                 for item in m['items']:
#                     if book in item['bookName']:
#                         for i in names:
#                             problem = f'{question}{i}'
#                             if item['problem'] == problem and (item['chapter'] == chapter or item['problem'] == question):
#                                 print('Chapter found:', item['chapter'])
#                                 print(f'Here is the guide to the solution to question {question}')
#                                 link = item['link']
#                                 found = True
#                                 return link
#                                 break
#                             else:
#                                 continue
#             elif resp == 'n' or resp == 'no':
#                 print('Please specify the textbook name again, but be more specific with respect to the textbook official name')
#                 break

#         if found:
#             break
#         else:
#             p += 1
#             print(p)

# Example usage of the function
# book_input = input('Book: ')
# chapter_input = input('Chapter: ')
# question_input = input('Question: ')

# get_textbook_info(book_input, chapter_input, question_input)








# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
#     'authorization': 'wixcode-pub.18385fb311792b7a2cd1f9c7d69d21ac6e1417fc.eyJpbnN0YW5jZUlkIjoiMDUzZDZjZjgtYzM1Yi00MWI3LTk4ZDItNTkwMWQ4YjM0NmI5IiwiaHRtbFNpdGVJZCI6ImM2ZThlNTM2LWY4NDEtNGYwMi05NWNhLTgyNmRjYzczNzA3MCIsInVpZCI6bnVsbCwicGVybWlzc2lvbnMiOm51bGwsImlzVGVtcGxhdGUiOmZhbHNlLCJzaWduRGF0ZSI6MTY5NTQwMDMzOTI4MiwiYWlkIjoiMjZmNjg1NDMtMTg2Ny00MTU2LTk3ZmEtMjg0ZDdiMTc5MzdiIiwiYXBwRGVmSWQiOiJDbG91ZFNpdGVFeHRlbnNpb24iLCJpc0FkbWluIjpmYWxzZSwibWV0YVNpdGVJZCI6IjNkYjk3OTJmLTliYWYtNDg0Ny05ZGIxLWI2ZDVjYzc5YWIwZiIsImNhY2hlIjpudWxsLCJleHBpcmF0aW9uRGF0ZSI6bnVsbCwicHJlbWl1bUFzc2V0cyI6IlNob3dXaXhXaGlsZUxvYWRpbmcsSGFzRG9tYWluLEFkc0ZyZWUiLCJ0ZW5hbnQiOm51bGwsInNpdGVPd25lcklkIjoiNzNkZmY5YmMtZDRjNy00YjQ2LTg1OTEtNTM0YzBkNmFlYjE1IiwiaW5zdGFuY2VUeXBlIjoicHViIiwic2l0ZU1lbWJlcklkIjpudWxsLCJwZXJtaXNzaW9uU2NvcGUiOm51bGwsImxvZ2luQWNjb3VudElkIjpudWxsLCJpc0xvZ2luQWNjb3VudE93bmVyIjpudWxsfQ==',
#     'Content-Type': 'application/json',
#     'Accept': 'application/json, text/plain, */*',
#     'Referer': 'https://www.litsolutions.org/_partials/wix-thunderbolt/dist/clientWorker.b151dd12.bundle.min.js',
#     'commonConfig': '%7B%22brand%22%3A%22wix%22%2C%22host%22%3A%22VIEWER%22%2C%22BSI%22%3A%221ddd14da-29be-45c5-92f6-53a98832da67%7C10%22%7D',
#     'x-wix-brand': 'wix',
#     'X-Wix-Client-Artifact-Id': 'wix-thunderbolt',
# }

# book = input(str('Book: '))
# chapter = input(str('Chapter: '))
# question = input(str('Question: '))

# names = ['RQ', 'P', 'E', 'SP']

# p = 1
# found = False
# while True:
#     json_data = {
#         'collectionName': f'dsd{p}', #dsd25,dsd14  change the last 2 numbers to get different collections
#         'dataQuery': {
#             'filter': {
#                 '$and': [
#                     {
#                         'bookName': {
#                             '$contains': book
#                         },
#                         'fileName': {
#                             '$contains': f'Chapter {chapter}',
#                         },
#                     },
#                 ],
#             },
#             'paging': {
#                 'offset': 0,
#             },
#             'fields': [],
#         },
#         'options': {},
#         'includeReferencedItems': [],
#         'segment': 'LIVE',
#         'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
#     }

#     response = requests.post(
#         'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
#         headers=headers,
#         json=json_data,
#     )
#     print(response.status_code)

#     m = json.loads(response.text)
#     print(m)

#     if len(m['items']) > 1:
#         print(f'Is this the textbook you specified: {m['items'][0]['bookName']}')
#         resp = input("Y or N: ") ## Make the input lowercase

#         if resp == 'y' or resp == 'yes':
#             for item in m['items']:  # Iterate over the 'items' list
#                 if book in item['bookName']:
#                     # print('Book found:', item['bookName'])
#                     # print('Chapter found:', item['chapter'])
#                     # print('Link:', item['link'])
#                     for i in names:
#                         problem = f'{question}{i}'
#                         if item['problem'] == problem and item['chapter'] == chapter or item['problem'] == question:
#                             print('Chapter found:', item['chapter'])
#                             print(f'Here is the guide to the solution to question {question}')
#                             link = item['link']
#                             print(link)
#                             found = True
#                             break
#                         else:
#                             continue
                
    
#         elif resp == 'n' or resp == 'no':
#             print('Please specify the textbook name again, but be more specific with respect to the textbook offical name')
#             break
#     # link = m['items'][0]['link']
#     if found:
#         break
#     else:
#         p += 1 
#         print(p)   
    




# while True:
#     json_data = {
#         'collectionName': f'dsd{p}', #dsd25,dsd14  change the last 2 numbers to get different collections
#         'dataQuery': {
#             'filter': {
#                 '$and': [
#                     {
#                         'bookName': {
#                             '$contains': book
#                         },
#                         'fileName': {
#                             '$contains': f'Chapter {chapter}, Problem 3RQ.png',
#                         },
#                     },
#                 ],
#             },
#             'paging': {
#                 'offset': 0,
#             },
#             'fields': [],
#         },
#         'options': {},
#         'includeReferencedItems': [],
#         'segment': 'LIVE',
#         'appId': '4e205879-9e5f-4e99-b394-d78c05874385',
#     }

#     response = requests.post(
#         'https://www.litsolutions.org/_api/cloud-data/v1/wix-data/collections/query',
#         headers=headers,
#         json=json_data,
#     )
#     print(response.status_code)

#     m = json.loads(response.text)
#     print(m)

#     for item in m['items']:  # Iterate over the 'items' list
#         if book in item['bookName']:
#             print('Book found:', item['bookName'])
#             print('Link:', item['link'])
#             link = item['link']
#             found = True
#             print(link)
#     # link = m['items'][0]['link']
#     if found:
#         break
#     else:
#         p += 1 
#         print(p)   