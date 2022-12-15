# Maintenance Notes

## The goal workflow

The ultimate goal for the website was to have automated, streamlined integration between GitHub/Discord:

- Create a bot/service that watches the `game-scores` channel for new boxscores.
- When a new game is posted, download the image and process it with an OCR library (such as [extracttable][1]).
- Push the extracted boxscore to the website.

In reality, though, there were a few challenges that kept this from happening.

## Message inconsistency

![Screen Shot 2022-09-09 at 9 59 09 AM](https://user-images.githubusercontent.com/8785025/189402899-6e5b75e1-cbe1-4426-8dea-68237ab2c651.png)

A post like the one above is ideal: it provides the names of both teams and then image of the boxscore. However, 
because there's no standard post structure, it's hard to automate the process of extracting information.

## Image quality

Low resolution or off-center screenshots make the OCR process unreliable.

[1]: https://www.extracttable.com/