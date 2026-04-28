import json
  import os

  cloud_path = os.path.expanduser("~/.hermes/auth.json")

  with open(cloud_path, "r") as f:
      cloud = json.load(f)

  # 备份
  with open(cloud_path + ".bak", "w") as f:
      json.dump(cloud, f, indent=2)

  # WSL 的 openai-codex provider 数据
  cloud["providers"]["openai-codex"] = {
      "tokens": {
          "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfRU1vYW1FRVo3M
  2YwQ2tYYVhwN2hyYW5uIiwiZXhwIjoxNzc4MTI1Nzk3LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsiY2hhdGdwdF9hY2NvdW50X2lkIjoiZjVlNTkwNjAtYmVhYS00MzMyLWFlNTAtM2ZiOTg0NWQyZWI5IiwiY2hhdGdwdF9hY2NvdW50X3VzZXJfaWQiOiJ1c2Vy
  LXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5S19fZjVlNTkwNjAtYmVhYS00MzMyLWFlNTAtM2ZiOTg0NWQyZWI5IiwiY2hhdGdwdF9jb21wdXRlX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X3BsYW5fdHlwZSI6InBsdXMiLCJjaGF0Z3B0X3VzZXJfaWQiOiJ
  1c2VyLXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5SyIsInVzZXJfaWQiOiJ1c2VyLXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5SyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJmYXllbHV5dWFuQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIj
  p0cnVlfSwiaWF0IjoxNzc3MjYxNzk2LCJpc3MiOiJodHRwczovL2F1dGgub3BlbmFpLmNvbSIsImp0aSI6IjNjYWE2NmIyLTZhODEtNGUwMy04ZTcwLWRmNDQ1ZjYyMzI5NiIsIm5iZiI6MTc3NzI2MTc5NiwicHdkX2F1dGhfdGltZSI6MTc3NzI2MTc3NDczNiwic2NwIjpbI
  m9wZW5pZCIsInByb2ZpbGUiLCJlbWFpbCIsIm9mZmxpbmVfYWNjZXNzIl0sInNlc3Npb25faWQiOiJhdXRoc2Vzc19NZG9NR0I4a3JmQ3F1ZmNPWDFVRG5kR00iLCJzbCI6dHJ1ZSwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMTA4NTY3NjM0NjM1OTM3MTc2NzcifQ.y3llLMDNM
  ZB1rakZoGZ_Sv2ci0Cugs1oTQ7OGARj0HpZN9m6gWIsSlZfwaAtrlZHEnQfeFkFTrvhYRqorUhp05PtU5Eo_kX7KiD1ucAifobgY9WPPq759_VyUphpFESedn7zKF9g8j76011OCfI1xPs5KRei1i0Z8lSKx4TwwtgwShsMory4Oc0RyrJ-noUJn8WOqatF6LWRxtGjcJimUTet
  yTkHurbq5bfMM6_GAqG5loAC4A4KNXhwJukVshlExijoiyz2ANCpMgR33mSSCGPHw6IVbgksfOlTrVUiDbO9B_TYCmrMWcRNE4GvC-K58Hzn_RWbuxQRdMnuhwW-PjWclxzAXZ0D8LP6Z86SEsTJEz7Xmjfzovldxiy3WHYY-BHf_BuyKYTJ00UFpBZbuZ4Vvvx7a5r4Sa34tg6
  KJcVAK6sTHobVoJsXHFMPVkTg4Ne9oIl4w02VszT2q0tOLAEQGozbr2AalEaLff9vT7caNvGh1bbc_wAMfL12QhGaCBBmu1XVymGloVM-nB4YpY5v0tM7TfZU33nPjPryol3J5_kBjlKMGJflXR_1nQMO1MG2_Vtsw3ZZYOWUP3ZvtmsFMZ1CGhrsLKGyu6QnIe7DzSdl3caHi1
  DVDLZhWR1QUkmCjLX7D9AZ0eXYM9WvQJaYbj7Ge3CGaQJfEXzej_E",
          "refresh_token": "rt_iOKjsnXU1n80bVArSzY9VdV8b_Fvrq6yF5H4lU3ujS0.h_aQIte3V2FRnPyb8tzSLzdLeMW2MCydrPbHOoqu-jU"
      },
      "last_refresh": "2026-04-27T03:49:57.817762Z",
      "auth_mode": "chatgpt"
  }

  cloud["credential_pool"]["openai-codex"] = [
      {
          "id": "ff4ce8",
          "label": "openai-codex",
          "auth_type": "oauth",
          "priority": 0,
          "source": "manual:device_code",
          "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfRU1vYW1FRVo3M
  2YwQ2tYYVhwN2hyYW5uIiwiZXhwIjoxNzc4MDg0MjAzLCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsiY2hhdGdwdF9hY2NvdW50X2lkIjoiZjVlNTkwNjAtYmVhYS00MzMyLWFlNTAtM2ZiOTg0NWQyZWI5IiwiY2hhdGdwdF9hY2NvdW50X3VzZXJfaWQiOiJ1c2Vy
  LXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5S19fZjVlNTkwNjAtYmVhYS00MzMyLWFlNTAtM2ZiOTg0NWQyZWI5IiwiY2hhdGdwdF9jb21wdXRlX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X3BsYW5fdHlwZSI6InBsdXMiLCJjaGF0Z3B0X3VzZXJfaWQiOiJ
  1c2VyLXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5SyIsInVzZXJfaWQiOiJ1c2VyLXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5SyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJmYXllbHV5dWFuQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIj
  p0cnVlfSwiaWF0IjoxNzc3MjIwMjAzLCJpc3MiOiJodHRwczovL2F1dGgub3BlbmFpLmNvbSIsImp0aSI6IjY4ODJhMmNmLTNkNGQtNDcyYi05MzMyLTdiM2MxMjZmN2EyOSIsIm5iZiI6MTc3MjIwMjAzLCJwd2RfYXV0aF90aW1lIjoxNzc3MjIwMTc3MzExLCJzY3AiOlsib
  3BlbmlkIiwicHJvZmlsZSIsImVtYWlsIiwib2ZmbGluZV9hY2Nlc3MiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzXzhPbDJISjZpTVlNSHkwOTI3TEFmc3E2bSIsInNsIjp0cnVlLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMDg1Njc2MzQ2MzU5MzcxNzY3NyJ9.R_TFSOagt-F
  dgVzbKQtXKV2htQVRxJnIajcWMKQxzEXBum_dW1VCMlkrXGyKmFLA_Y1arhw8mgVZm7ZdafxhSg0sO1WGv6Cv9nk8fbzvw5O06SHX6IUHMx-E9I0AsG6L0YtQhweshx8LTjsy8EgGO9fV4t6tEafk3FimR_KWCPSRYGyAtNa949CWZyw-Dy4EDkSx1fWT6L74d1FuzTBn4vbHOK
  08e4I_59FzJxKvZ4Jpu46TwJ-tabH6XLzWtuDfq-VTYbibGwa3RkRWEmfAkK-BI4jDKkRKHeBl3AsXCiur_VhOgeq8uCqFOEeg0HxQlYzBFJ5lw1jsf-psjC5Lbp3wtLqI63X6eCweAq7KWCj3PyAgi9zMfcymJSFuo60AHHBBiEtBjtNMX8chx5elofB1Ci89AWYtNyVq5FlDj
  xnUy4cvax5aVPwUJVkEsV03pQHptic8-NXH3EgPZUV9py1StWRT2cDIwWLY8zgBdPLOojrdnWMTZJ0hJMuR3Hj1ReeoTqQru6Yo9bbBwZYLbxYl6-hwBdBJnZEDLp_KsSN0PZiZR08GTz196oRKvUM38qqS0NBA9e3t16A3GY2jwp-8SmCojHArEpsWtWm_aw6TptCaJT0-PzS8
  4MvrppSvOGWna3ZbBYAemDOzj4hZdCj_9Yw66XOXGYJ1EOqWWDk",
          "refresh_token": "rt_ojgACEphyjh6uaMjrF9BVz8wnXox6WSY0xMFDhc9EbQ.do9QEX-2zKSxph5lB7cinhpxhVeZcwx-3sN4VQowMv8",
          "last_status": "ok",
          "last_status_at": None,
          "last_error_code": None,
          "last_error_reason": None,
          "last_error_message": None,
          "last_error_reset_at": None,
          "base_url": "https://chatgpt.com/backend-api/codex",
          "last_refresh": "2026-04-26T16:16:44.311311Z",
          "request_count": 0
      },
      {
          "id": "27e0d5",
          "label": "device_code",
          "auth_type": "oauth",
          "priority": 1,
          "source": "device_code",
          "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfRU1vYW1FRVo3M
  2YwQ2tYYVhwN2hyYW5uIiwiZXhwIjoxNzc4MTI1Nzk3LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsiY2hhdGdwdF9hY2NvdW50X2lkIjoiZjVlNTkwNjAtYmVhYS00MzMyLWFlNTAtM2ZiOTg0NWQyZWI5IiwiY2hhdGdwdF9hY2NvdW50X3VzZXJfaWQiOiJ1c2Vy
  LXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5S19fZjVlNTkwNjAtYmVhYS00MzMyLWFlNTAtM2ZiOTg0NWQyZWI5IiwiY2hhdGdwdF9jb21wdXRlX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X3BsYW5fdHlwZSI6InBsdXMiLCJjaGF0Z3B0X3VzZXJfaWQiOiJ
  1c2VyLXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5SyIsInVzZXJfaWQiOiJ1c2VyLXhWdU5YYklXNERhYkNIZnZGV1ZJODZ5SyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJmYXllbHV5dWFuQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIj
  p0cnVlfSwiaWF0IjoxNzc3MjYxNzk2LCJpc3MiOiJodHRwczovL2F1dGgub3BlbmFpLmNvbSIsImp0aSI6IjNjYWE2NmIyLTZhODEtNGUwMy04ZTcwLWRmNDQ1ZjYyMzI5NiIsIm5iZiI6MTc3NzI2MTc5NiwicHdkX2F1dGhfdGltZSI6MTc3NzI2MTc3NDczNiwic2NwIjpbI
  m9wZW5pZCIsInByb2ZpbGUiLCJlbWFpbCIsIm9mZmxpbmVfYWNjZXNzIl0sInNlc3Npb25faWQiOiJhdXRoc2Vzc19NZG9NR0I4a3JmQ3F1ZmNPWDFVRG5kR00iLCJzbCI6dHJ1ZSwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMTA4NTY3NjM0NjM1OTM3MTc2NzcifQ.y3llLMDNM
  ZB1rakZoGZ_Sv2ci0Cugs1oTQ7OGARj0HpZN9m6gWIsSlZfwaAtrlZHEnQfeFkFTrvhYRqorUhp05PtU5Eo_kX7KiD1ucAifobgY9WPPq759_VyUphpFESedn7zKF9g8j76011OCfI1xPs5KRei1i0Z8lSKx4TwwtgwShsMory4Oc0RyrJ-noUJn8WOqatF6LWRxtGjcJimUTet
  yTkHurbq5bfMM6_GAqG5loAC4A4KNXhwJukVshlExijoiyz2ANCpMgR33mSSCGPHw6IVbgksfOlTrVUiDbO9B_TYCmrMWcRNE4GvC-K58Hzn_RWbuxQRdMnuhwW-PjWclxzAXZ0D8LP6Z86SEsTJEz7Xmjfzovldxiy3WHYY-BHf_BuyKYTJ00UFpBZbuZ4Vvvx7a5r4Sa34tg6
  KJcVAK6sTHobVoJsXHFMPVkTg4Ne9oIl4w02VszT2q0tOLAEQGozbr2AalEaLff9vT7caNvGh1bbc_wAMfL12QhGaCBBmu1XVymGloVM-nB4YpY5v0tM7TfZU33nPjPryol3J5_kBjlKMGJflXR_1nQMO1MG2_Vtsw3ZZYOWUP3ZvtmsFMZ1CGhrsLKGyu6QnIe7DzSdl3caHi1
  DVDLZhWR1QUkmCjLX7D9AZ0eXYM9WvQJaYbj7Ge3CGaQJfEXzej_E",
          "refresh_token": "rt_iOKjsnXU1n80bVArSzY9VdV8b_Fvrq6yF5H4lU3ujS0.h_aQIte3V2FRnPyb8tzSLzdLeMW2MCydrPbHOoqu-jU",
          "last_status": "ok",
          "last_status_at": None,
          "last_error_code": None,
          "last_error_reason": None,
          "last_error_message": None,
          "last_error_reset_at": None,
          "base_url": "https://chatgpt.com/backend-api/codex",
          "last_refresh": "2026-04-27T03:49:57.817762Z",
          "request_count": 0
      }
  ]

  with open(cloud_path, "w") as f:
      json.dump(cloud, f, indent=2)

  print("OK 合并完成")
  print("providers:", list(cloud["providers"].keys()))
  print("credential_pool:", list(cloud["credential_pool"].keys()))
