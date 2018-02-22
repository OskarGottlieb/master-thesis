import logwood

import modules.god



logwood.basic_config(level = logwood.INFO)
		

if __name__ == '__main__':
	GOD = modules.god.God()
	GOD.run_simulation()