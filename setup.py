from setuptools import find_packages, setup

setup(
    name="AsyncSpider",
    version="0.2.0",
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
    ],
    license='Apache License',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False
)
