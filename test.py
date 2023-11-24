message = input("Enter message: ")
hash_n = (120 - len(message))//2

print('#'*hash_n + message + '#'*hash_n)