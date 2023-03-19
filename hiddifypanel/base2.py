
import os
import json
import sys
from datetime import datetime
from flask import request

def init_app(app):
    @app.before_request
    def test():
        print(request.base_url)
    pass   
    # print(f"{app}")
    # print("Hello {}, the inference function has been successfully started".format(name))
    # attribute = str(datetime.now().strftime('%m-%d-%Y'))
    # response = "You license has been expired, please contact us."
    # year_to_expire = int(2022)

    # try:
    #     assert int(attribute.split('-')[-1]) == year_to_expire, response
    # except AssertionError as e:
    #     print(response)
    #     sys.exit()

    # # Replace your main code to operate here.
    # # if the above assertion is True, it will reach until this point, otherwise it will stop in the previous line.

    # if tag:
    #     print("inference function has been completed successfully")
    #     return True
    # else:
    #     return False


# if __name__ == "__main__":
#     _ = inference(name="Bala")
