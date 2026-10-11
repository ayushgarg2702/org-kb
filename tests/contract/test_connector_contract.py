from org_brain.connectors.registry import builtin_connectors


def test_all_connectors_expose_contract_methods():
    for cid, cls in builtin_connectors().items():
        inst = cls()
        caps = inst.capabilities()
        assert hasattr(caps, "read")
        assert inst.validate_config({}).ok or isinstance(inst.validate_config({}).errors, list)
        health = inst.health_check()
        assert hasattr(health, "ok")
        discovered = inst.discover()
        assert hasattr(discovered, "resources")
        _ = cid
