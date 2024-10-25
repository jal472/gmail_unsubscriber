# gmail_unsubscriber
## Description
Using the gmail api to unsubscribe from unwanted marketing emails.

## Following the GMail API Documentation here:
[https://developers.google.com/gmail/api/quickstart/python](https://developers.google.com/gmail/api/guides)

## This resource helped me understand how to build a service in the gmail api
[https://googleapis.github.io/google-api-python-client/docs/start.html#building-and-calling-a-service](https://googleapis.github.io/google-api-python-client/docs/start.html#building-and-calling-a-service)

## Update: 10/19
Currently able to request the unsubscribe link from marketing emails but there is no guarantee that simply accessing the link will unsubscribe from the marketing emails in the future. My next thought was to use selenium to scrape the form at the next step, fill it out, and submit. The problem here is that not all unsubscribe forms are the same and may require different things such as unchecking radio buttons to stop certain marketing emails or simply entering your email in a text edit and then submitting. This made me take a break from the project. One day I was studying for my AWS Certified Cloud Practitioner Exam and I came accross the AI section. There was a mention of LLMs and then I had the thought "ChatGPT could easily tell me what needs to be filled out in the form in order to successfully unsubscribe from future marketing emails". And so now, my idea is to integrate Google's Gemini API (since it is free and ChatGPT and Claude are not) into the project to handle telling me what needs to be filled out in the form. Then I can use selenium to fill it out, submit, and we are on our way. Stay tuned, I am once again excited to work on this project.

## Selenium and Google Gemini Integration
Testing can be done visually to ensure it is working first but for the final product we should use a headless browser so it seems like magic to the user.

Use selenium with a headless browser: https://www.browserstack.com/guide/headless-browser-testing-selenium-python#:~:text=Headless%20browser%20testing%20using%20Selenium%20and%20Python%20is%20a%20technique,it%20runs%20in%20the%20background.
