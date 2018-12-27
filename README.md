# token_backend
Backend that powered my senior capstone project. This project could be used in many different ways but its main use is to provide ease of access to the Ethereum platform for issuing contracts that interface with the ERC 720 spec.

Majority of backend python code was designed and implemented by me. I did not design or implement any of the html sections besides the "documentation.html". Most of the logic is within the /routes/*.py, and /models/*.py files. (I did not write the analytics.py file)

***
This project can be run in debug mode like any other flask app. "./python TOKER.py" should do the trick. To access the documentation for the application visit localhost:8088/docs after running the application.
***

### Things I would of changed?
* Unified the model objects accross the application.  
  * I often repeated model objects depending on if I am sending or parsing data. I should of defined the most common objects and used them across the app. 
  * I think this problem could of been solved it I spent more time understanding the marshmallow library and the power it brings.
* Better error handling.  
  * For the most part the application handles errors well but there are certain contexts in which a request will get responded to with a stacktrace. (For development this is fine but in a production environment this would be unacceptable.)
  * This could be solved with better unit test coverage.
* Unit tests
  * I did not make use of unit tests for this project which there is no excuse for. Writing them would of been very useful for regression testing.
