import logwood

import modules.god



logwood.basic_config(level = logwood.INFO)
		

def main() -> None:
	responses = []
	for i in range(10):
		GOD = modules.god.God()
		responses.append(GOD.run_simulation())
	return responses


if __name__ == '__main__':
	main()
