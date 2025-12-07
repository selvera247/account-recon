# Analytics Intake Frontend

This folder contains the HTML intake form for Data Analytics / Revenue PMO requests.

## How it works

- The form POSTs directly to a Google Apps Script Web App URL.
- The Apps Script writes each submission as a row into a Google Sheet (`Intake` tab).

## Steps to use

1. Deploy your Apps Script Web App and copy its URL.
2. Open `index.html` and replace:

   ```html
   <form action="YOUR_WEB_APP_URL_HERE" method="POST" id="dataForm">