from jose import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDdhYWMzMC1jMjc2LTRkMjctYWZkNy02MjRiNzk3NWZiMDciLCJleHAiOjE3NTQxNDA5MjR9.Q59CrZ9L5xjMxJ7pDOSUzz0cjflTpbhrgXltU6ox73w"

SECRET_KEY = "4a2bd44e4aa14cf295c36a5371c3fd55a0f4e2c927ea48cb9d34d2b7e76a99a4"

decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
