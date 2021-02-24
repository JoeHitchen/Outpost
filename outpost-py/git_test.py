import gateway


git_fetch = gateway.request_git_fetch.delay('repo').wait()

print(git_fetch)


