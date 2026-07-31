from fortwall_pool import clustering


def _categorized():
    # Two well-separated pairs; all sets distinct so URL lookup is 1:1.
    return [
        {"associated_numbers": [1, 2, 3], "urls": ["/a"]},
        {"associated_numbers": [1, 2, 3, 4], "urls": ["/b"]},
        {"associated_numbers": [20, 21], "urls": ["/c"]},
        {"associated_numbers": [20, 21, 22], "urls": ["/d"]},
    ]


def test_run_clustering_separates_two_groups():
    result = clustering.run_clustering(_categorized(), num_clusters=2)

    assert result.num_clusters == 2
    # Superset content is order-independent across the two clusters.
    supersets = {frozenset(s) for s in result.supersets}
    assert supersets == {frozenset({1, 2, 3, 4}), frozenset({20, 21, 22})}

    # URLs of each true group stay together.
    url_groups = {frozenset(v) for v in result.cluster_urls.values()}
    assert url_groups == {frozenset({"/a", "/b"}), frozenset({"/c", "/d"})}


def test_superset_is_union_of_members():
    result = clustering.run_clustering(_categorized(), num_clusters=2)
    for cid, members in result.clusters_syscalls.items():
        union = set().union(*members) if members else set()
        assert result.supersets[cid] == union


def test_cluster_wrapper_matches_run_clustering():
    cats = _categorized()
    supersets, cluster_urls, clusters_syscalls = clustering.cluster(cats, num_clusters=2)
    result = clustering.run_clustering(cats, num_clusters=2)
    assert supersets == result.supersets
    assert cluster_urls == result.cluster_urls


def test_diagnostics_lines_shape_and_quirk():
    result = clustering.run_clustering(_categorized(), num_clusters=2)
    lines = clustering.diagnostics_lines(result)
    text = "\n".join(lines)
    assert "Superset 1:" in text
    assert "Cluster 1:" in text
    # Preserved quirk: sensitive-syscall figure is always 0.00%.
    assert "Max of sensitive syscalls: 0.00% of sensitive syscalls" in text
