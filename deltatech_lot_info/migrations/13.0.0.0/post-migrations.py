def migrate(cr, version):
    cr.execute(
        """
        INSERT INTO  stock_lots_tag (id, name) SELECT id, name FROM stock_quant_tag;
        DELETE FROM  stock_quant_tag;
    """
    )
