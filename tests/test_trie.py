"""This file tests the main.editor.Intellisense.Trie instance"""

from .context import Trie

def test_trie_create():
    trie = Trie()
    assert trie.parent is None
    assert len(trie) == 0
    assert trie.value() is None
    assert not trie.final

    trie = Trie("test")
    assert trie.parent is None
    assert len(trie) == 1
    assert trie.value() is None
    assert not trie.final

def test_trie_insert():
    trie = Trie("test")
    l = trie.list()
    assert len(l) == 1
    assert l[0].key() == "test"

def test_trie_find():
    words = ["test", "abc", "testing", "triumpf", "abbreviation"]
    trie = Trie()
    for word in words:
        trie.insert(word, word)
    for word in words:
        found = trie.find(word)
        assert word == found.value() == found.key()
    res = trie.find('')
    assert res is not None
    res = res.keys()
    for word in words:
        assert word in res

