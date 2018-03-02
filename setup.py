from setuptools import find_packages, setup


def get_version():
    with open('AsyncSpider\__init__.py', 'r', encoding='utf8') as f:
        while True:
            line = f.readline()
            if line.startswith('__version__'):
                break
    return line.split('=')[1].split("'")[1]


if __name__ == '__main__':
    setup(
        name="AsyncSpider",
        version=get_version(),
        description="Async Spider Framework",
        author="Nugine",
        author_email="Nugine@163.com",
        url='https://github.com/Nugine/AsyncSpider',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3.6',
        ],
        install_requires=[
            'aiohttp',
            'chardet',
            'fake_useragent',
        ],
        license='Apache License',
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False
    )
