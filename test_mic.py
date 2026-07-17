import speech_recognition as sr

print("Lista de micrófonos detectados por Python:")
print("-" * 40)
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"[{index}] {name}")
print("-" * 40)
print("Si tu audífono no es el micrófono 'Predeterminado' de Windows,")
print("Python no podrá escucharte correctamente.")
