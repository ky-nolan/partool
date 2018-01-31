import argparse

def main(*args,**kwargs):
	for k,v in enumerate(kwargs):
		print('kwargs =',v,kwargs[v])
	for arg in args:
		print('args =',arg)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-t',action="store_true", default=False)
	args, unknown = parser.parse_known_args()
	main(args,**dict(kwarg.split('=') for kwarg in unknown))