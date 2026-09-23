# my personal website!

hi! this is the github repo for my personal website. 

fair warning: this website was made with the intent of nobody but me seeing it's inner workings, so some of the comments or codepaths are a bit nonsensical to people who aren't me

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/05e7f461-b865-4006-a468-f973c30c2bd1" />

## tech

the backend is written in Flask, with SQLite being used to store blog entries. 

the frontend is plain-old HTML/CSS

fun fact: there is no javascript here! (excluding the CAPTCHA for posting visitor messages, it's safer just to trust Cloudflare on that)

## features

- visitor wall: visitors can submit messages that are then approved for publishing by the webadmin
- project list: dynamically add/remove projects to show off, stored in database
- journal/blog: markdown-formatted blog posts
- status & time: shows the time in my timezone (CT), the status is just a guess on whether i'm awake based on that time
- custom routes: basically a url shortener for the webadmin, very useful for bodging together other projects or keeping a stable url for a changing target
- dynamically loaded 88x31 buttons
