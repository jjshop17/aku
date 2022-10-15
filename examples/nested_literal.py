from typing import List, Literal

from aku import Aku

app = Aku()


@app.option
def foo(x: List[Literal['a', 'i', 'u', 'e', 'o']]):
    print(f'x => {x}')


if __name__ == '__main__':
    app.run()